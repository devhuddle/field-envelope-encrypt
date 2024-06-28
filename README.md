# Field Envelope Encrypt

## Overview
This library provides a simple class decorator that will encrypt and decrypt fields on an SQLAlchemy model. This is useful when you want to encrypt certain fields on a model but still want to be able to read and write to those fields natively.

## Installation
```bash
pip install field-envelope-encrypt
```

## Usage
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
