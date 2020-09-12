import datetime
import json
import pytz
from dateutil import tz

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    Float,
    func,
    )

from .models import DBSession, Sale, Product

class SalesViews(object):
    def __init__(self, request):
        self.request = request

    @view_config(route_name='home', renderer='home.pt')
    def home(self):
        sales = DBSession.query(Sale).join(Product, Sale.uid==Product.sale_id)
        sales = sales.add_column(func.sum(Product.price*Product.amount).label('t_price')).\
                group_by(Product.sale_id).all()

        total_price = 0
        # Конвертируем дату, считаем total_price 
        p_sales = []
        for sale in sales:
            r = sale[0].__dict__
            r['price'] = sale[1]
            total_price += r['price']
            # Конвертируем в местную timezone
            r['date'] = r['date'].replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
            r['date'] = r['date'].strftime('%Y-%m-%d, %z')
            p_sales.append(r)
        return dict(title='Homepage', sales=p_sales, total_price=total_price)

    @view_config(route_name='products', renderer='products.pt')
    def products(self):
        products = DBSession.query(Product).order_by(Product.uid)
        return dict(products=products)
    
    @view_config(route_name='new_sale', renderer='new_sale.pt')
    def new_sale(self):
        # Специальный случай, может понадобиться в дальнейшем
        if 'create_new_product' in self.request.params:
            return dict(title='Новая продажа', products=self.request.params['create_new_product'])

        # Проверяем, были ли отправлены данные для создания продажи
        if 'num' in self.request.params:
            num = self.request.params['num']
            date_str = self.request.params['date']
            products_str = self.request.params['products']
            products = {}

            # Товары
            if products_str != '':
                products = json.loads(products_str)

            # Дата
            if date_str != '':
                d = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                timezone = pytz.timezone("Europe/Moscow")
                date = timezone.localize(d)
            else:
                # На всякий случай
                date = datetime.today()

            # Проверяем, существует ли продажа с таким номером
            if DBSession.query(Sale).filter(Sale.num==num).scalar() is not None:
                # Редирект на страницу с ошибкой
                url_warning = self.request.route_url('error_already_exists')
                return HTTPFound(url_warning)
            
            # Создаем продажу
            model = Sale(num=num, date=date)
            DBSession.add(model)

            # Определяем uid продажи
            sale_id = DBSession.query(Sale).filter(Sale.num==num)[0].__dict__['uid']

            # Создаем товары
            for i in products:
                p = products[i]
                
                p_name = p['product']
                price = float(p['price'])
                amount = float(p['amount'])
                
                model = Product(sale_id=sale_id, product=p_name, price=price, amount=amount)
                DBSession.add(model)

            url_home = self.request.route_url('home')
            return HTTPFound(url_home)
        return dict(title='Новая продажа', products={})

    @view_config(route_name='sale', renderer='sale.pt')
    def sale(self):
        uid = str(self.request.matchdict['uid'])
        sales = DBSession.query(Sale).filter(Sale.uid==uid)

        # Проверяем, существует ли такая продажа
        if sales.count() < 1:
            url_error = self.request.route_url('error_doesnt_exist')
            return HTTPFound(url_error)
        sale = sales[0].__dict__
        
        # Конвертируем дату в местную timezone
        sale['date'] = sale['date'].replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
        sale['date'] = sale['date'].strftime('%Y-%m-%d, %z')
        
        products = DBSession.query(Product).filter(Product.sale_id==uid).order_by(Product.uid)

        # Считаем общую стоимость
        total_price = 0
        for product in products :
            total_price += product.__dict__['price'] * product.__dict__['amount']
        return dict(sale=sale, products=products, total_price=total_price)
    
    @view_config(route_name='error_doesnt_exist', renderer='error_doesnt_exist.pt')
    def error_doesnt_exist(self):
        return {}

    @view_config(route_name='error_already_exists', renderer='error_already_exists.pt')
    def error_already_exists(self):
        return {}

    @view_config(route_name='delete')
    def delete(self):
        uid = self.request.params['uid']
        DBSession.query(Sale).filter(Sale.uid == uid).delete()
        DBSession.query(Product).filter(Product.sale_id == uid).delete()
        url_home = self.request.route_url('home')
        return HTTPFound(url_home)
