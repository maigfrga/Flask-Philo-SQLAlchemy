from flask_philo_sqlalchemy.test import SQLAlchemyTestCase
from flask_philo_sqlalchemy.http import SQLAlchemyView
from sqlalchemy import Column, String
from flask_philo_core.test import BaseTestFactory
from flask_philo_sqlalchemy.orm import BaseModel
from flask_philo_sqlalchemy.exceptions import NotFoundError
from flask import json, request


class User(BaseModel):
    __tablename__ = 'user_test_views'
    username = Column(String(64))


class ModelFactory(BaseTestFactory):

    @classmethod
    def create_user(self):
        user = User(username=self.create_unique_string())
        user.add()
        user.objects.pool.commit()
        return user


class UserResourceView(SQLAlchemyView):

    def get(self, id=None):

        try:
            if id is not None:

                user = User.objects.get(id=id)
                data = {'id': user.id, 'username': user.username}
            else:
                data = [
                   {'id': user.id, 'username': user.username}
                   for user in User.objects.filter_by()
                ]
            return self.json_response(status=200, data=data)
        except NotFoundError:
            return self.json_response(status=404)

    def post(self):
        obj = User(**request.json)
        obj.add()
        self.sqlalchemy_pool.commit()
        data = {'id': obj.id}
        return self.json_response(status=201, data=data)

    def put(self, id=None):
        obj = User.objects.get_for_update(id=id)
        obj.username = request.json['username']
        obj.update()
        self.sqlalchemy_pool.commit()
        obj = User.objects.get(id=id)
        data = {'id': obj.id, 'username': obj.username}
        return self.json_response(status=200, data=data)

    def delete(self, id=None):
        obj = User.objects.get(id=id)
        obj.delete()
        self.sqlalchemy_pool.commit()
        return self.json_response(status=200)


class TestCaseModel(SQLAlchemyTestCase):
    config = {
        'FLASK_PHILO_SQLALCHEMY': {
            'DEFAULT': 'postgresql://ds:dsps@pgdb:5432/ds_test',
        }
    }

    urls = (
        ('/users', UserResourceView, 'users'),
        ('/users/<int:id>', UserResourceView, 'user'),
    )

    def test_get(self):
        with self.app.app_context():
            assert 0 == User.objects.count()
            user1 = ModelFactory.create_user()
            user2 = ModelFactory.create_user()

            assert 2 == User.objects.count()
            client = self.app.test_client()

            result = client.get('/users/{}'.format(user1.id))
            assert 200 == result.status_code
            j_content = json.loads(result.get_data().decode('utf-8'))
            assert j_content['id'] == user1.id

            client = self.app.test_client()
            result2 = client.get('/users/{}'.format(user2.id))
            assert 200 == result2.status_code
            j_content2 = json.loads(result2.get_data().decode('utf-8'))
            assert j_content2['id'] == user2.id

            client = self.app.test_client()
            result3 = client.get('/users')
            assert 200 == result3.status_code
            j_content3 = json.loads(result3.get_data().decode('utf-8'))
            assert 2 == len(j_content3)

    def test_post(self):
        with self.app.app_context():
            assert 0 == User.objects.count()

            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            }
            data = json.dumps({'username': 'username'})
            client = self.app.test_client()
            result = client.post('/users', data=data, headers=headers)
            assert 201 == result.status_code
            assert 1 == User.objects.count()

    def test_put(self):
        with self.app.app_context():
            user = ModelFactory.create_user()
            assert 1 == User.objects.count()
            old_username = user.username

            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            }
            data = json.dumps({'username': 'newusername', 'id': user.id})
            url = 'users/{}'.format(user.id)

            client = self.app.test_client()
            result = client.put(url, data=data, headers=headers)
            assert 200 == result.status_code
            assert 1 == User.objects.count()
            j_content = json.loads(result.get_data().decode('utf-8'))

            assert j_content['id'] == user.id
            assert j_content['username'] != old_username
            assert j_content['username'] == 'newusername'

    def test_delete(self):
        with self.app.app_context():
            user1 = ModelFactory.create_user()
            assert 1 == User.objects.count()
            client = self.app.test_client()

            result = client.delete('/users/{}'.format(user1.id))
            assert 200 == result.status_code
            assert 0 == User.objects.count()
