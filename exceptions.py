class EmailExistsError(Exception):
    detail='user with this email exists'

class InvalidCredentialsError(Exception):
    detail = 'invalid email/password'

class ProductNameExistsError(Exception):
    detail='product name exists'

class ProductsValidationError(Exception):
    detail='one or more product not found'

class StockValidationError(Exception):
    detail='not available stock for one or more products'

class OrderNotFoundError(Exception):
    detail='order not found'

class StatusTransitionError(Exception):
    detail = 'transition not allowed for current order status'

class InvalidSubCredentials(Exception):
    detail = 'could not validate token credentials'

class CustomerNotFound(Exception):
    detail = 'customer from token credentials not found'

class SignatureError(Exception):
    detail='invalid token signature'

class ExpiredTokenError(Exception):
    detail='token expired'

class NoPermissionError(Exception):
    detail='no permission'