# Field Envelope Encrypt

## Overview
This library provides a simple class decorator that will encrypt and decrypt fields on an SQLAlchemy model. This is useful when you want to encrypt certain fields on a model but still want to be able to read and write to those fields natively.

## Installation
```bash
pip install field-envelope-encrypt
```

## Usage
Using the library is simple. Just decorate your SQLAlchemy model with `@encrypt_fields` and append `_encrypted` to the field name you want to encrypt. The library will automatically encrypt and decrypt the field for you.

### Column Type
By default, the column type storing the encrypted data must support serialization of the python `dict` type. If that is not possible, a custom serializer can be provided.


### Example
```python
from sqlalchemy import Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column

from field_envelope_encrypt import encrypt_fields

Base = declarative_base()

@encrypt_fields
class UserModel(Base):
    __tablename__ = "__users__"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    email_encrypted: Mapped[dict] = mapped_column(JSON)
    password_encrypted: Mapped[dict] = mapped_column(JSON)


...
# session = SQLAlchemy session
user = UserModel()
user.name = "John Doe"
user.email = "john@somewhere.com"
user.password = "password123"       # It's a secret to everyone!
session.add(user)
session.commit()
```

## Custom Serializer
If the default serializer does not work for your use case, you can provide a custom serializer to the `@encrypt_fields` decorator. The user-supplied serializer must implement the `Serializer` interface. The `Serializer` interface has two methods: `serialize` and `deserialize`. The `serialize` method should take a python `dict` and return a serializable object. The `deserialize` method should take a serializable object and return a python `dict`.
