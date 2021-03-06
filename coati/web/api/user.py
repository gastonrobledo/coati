from mongoengine import errors as mongo_errors
from flask import request, current_app
from flask.ext.restful import Resource

from coati.core.models.user import User
from coati.core.models.notification import UserNotification
from coati.web.api.auth import AuthResource, current_user
from coati.web.api.auth.decorators import require_authentication
from coati.web.api import errors as api_errors
from coati.web.api.mails import create_activation_email


def get_notifications(user):
    notifications = UserNotification.objects(user=user)
    results = []
    for n in notifications:
        if n.activity.author.id != user.id:
            results.append(n)
    results.sort(key=lambda x: x.activity.created_on, reverse=True)
    if request.args.get('total'):
        results = results[:int(request.args.get('total'))]
    return results


def get_user_for_request(user_id):
    """
    Get a user by ID
    :param user_id: Id of the User
    :return: User Instance
    """
    if user_id == 'me':
        # TODO: Find a better way to do this
        # Workaround: mongoengine can not always deal with proxies'
        return current_user._get_current_object()

    user = User.get_by_id(user_id)
    if not user:
        raise api_errors.MissingResource(
            api_errors.INVALID_USER_ID_MSG
        )
    return user


def create_user(user_data):
    """
    Creates a User instance with the given user data.
    If errors occur during validation, also returns an error JSON.
    :param user_data: The user's data.
    :return: Tuple in the form (user, errors).
    """
    errors_dic = {}

    user = User(
        first_name=user_data.get('first_name'),
        last_name=user_data.get('last_name'),
        email=user_data.get('email'),
        password=user_data.get('password'),
        active=False
    )

    try:
        user.validate()
    except mongo_errors.ValidationError as ex:
        errors_dic = ex.to_dict()

        errors_dic.update(
            _object=user_data
        )

    if User.is_duplicated_email(user.email):
        errors_dic.update(dict(email=api_errors.DUP_EMAIL_ERROR_MSG),
                          _object=user_data)

    token = current_app.token_handler.generate_access_token(user.email)
    user.activation_token = token

    return user, errors_dic


class UsersList(Resource):
    """
    User Resource
    """

    @require_authentication
    def get(self):
        """
        Returns the list of users
        :return: A List of json representing users.
        """
        return User.objects.all()

    def post(self):
        """
        Create user resource
        :return: a Created resource
        """
        user_data = request.get_json(silent=True)
        if not user_data:
            raise api_errors.InvalidAPIUsage(
                api_errors.INVALID_JSON_BODY_MSG
            )

        user, errors_dic = create_user(user_data)
        errors_list = []
        if errors_dic:
            errors_list.append(errors_dic)

        if errors_list:
            raise api_errors.InvalidAPIUsage(
                api_errors.VALIDATION_ERROR_MSG,
                payload=errors_list
            )

        user.save()
        create_activation_email(user)

        return user, 201


class UserSearch(AuthResource):
    """
    Search users
    """

    def get(self, query):
        """
        Return the list of users matching the query string.
        :param query: the query string to search for a user
        :return: List of json dict text, value
        """
        users = User.search(query=query)
        data = []
        for u in users:
            val = dict(text=u.email, value=str(u.pk))
            data.append(val)
        return data


class UserInstance(AuthResource):
    """
    User Resource
    """

    def get(self, user_id):
        """
        Get an instance of a user.
        :param user_id: ID of the user
        :return: a User Object
        """
        user = get_user_for_request(user_id)
        return user, 200

    def put(self, user_id):
        """
        Update Resource
        :param user_id: The User ID
        :return: Return a user instance updated
        """
        data = request.get_json(silent=True)
        if not data:
            raise api_errors.InvalidAPIUsage(api_errors.INVALID_JSON_BODY_MSG)

        user = get_user_for_request(user_id)
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.picture = data.get('picture', user.picture)
        user.email = data.get('email', user.email)

        user.save()

        return user, 200

    def delete(self, user_id):
        """
        Delete the user
        :param user_id: Id of the User
        :return: No Content
        """
        user = get_user_for_request(user_id)
        user.delete()
        return {}, 204


class UserActivate(Resource):
    """
    Activation Token Class
    """
    def post(self):
        """
        Activate a user based on a token
        :return: token auth
        """
        data = request.get_json(silent=True)
        if not data:
            raise api_errors.InvalidAPIUsage(
                api_errors.INVALID_JSON_BODY_MSG
            )

        user = User.get_by_activation_token(data.get('token'))
        if not user:
            raise api_errors.MissingResource(
                api_errors.ACTIVATION_INVALID_TOKEN_MSG
            )

        user.active = True
        user.save()

        tokens_dict = current_app.token_handler.generate_tokens_dict(
            user.pk
        )

        return tokens_dict, 200


class UserNotifications(Resource):
    """
    Notifications of a user
    """

    def get(self, user_id):
        """
        get the notifications for a user
        :param user_id: user id or me
        :return: list of notifications
        """
        user = get_user_for_request(user_id)
        return get_notifications(user), 200

    def put(self, user_id):
        """
        update as readed all the notification not read for a user
        :param user_id: user id or me
        :return: list of notifications
        """
        user = get_user_for_request(user_id)
        UserNotification.objects(user=user).update(set__viewed=True)
        return get_notifications(user), 200