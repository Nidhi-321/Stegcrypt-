# backend/app/schemas.py
from marshmallow import Schema, fields

class RegisterSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)
    public_key = fields.Str(required=False)

class LoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)

class MessageSendSchema(Schema):
    receiver_id = fields.Int(required=True)
    ciphertext = fields.Str(required=True)
