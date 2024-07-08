# Field Envelope Encryption for SQLAlchemy

## Overview
This library provides a simple class decorator that will encrypt and decrypt fields on an SQLAlchemy model. This is useful when you want to encrypt certain fields on a model but still want to abstract the details of encryption from the rest of the application.

[Blog post](https://devhuddle.ai/envelope-encryption-for-sqlalchemy-fields/) for those interested in a deeper dive.

### Envelope Encryption
Under the hood, envelope encryption is used to ensure that the data is encrypted securely. The library uses the `cryptography` library to handle the encryption and decryption of the fields. A user-supplied Key Encryption Key (KEK) is used to encrypt the Data Encryption Key (DEK), which in turn is used to encrypt the data. The DEK is stored alongside the encrypted data in the database.

## Installation
(PyPi coming soon)
```bash
pip install -e .
```

## Usage
Using the library is simple. Just decorate your SQLAlchemy model with `@encrypt_fields` and append `_encrypted` to field names you want to encrypt. When reading or writing to the model, use the field name *without* the `_encrypted` suffix.

**Example Model Declaration**
```python

# SECRET_KEY is likely fetched from an environment variable or secret storage
@encrypt_fields(kek=SECRET_KEY)
class UserModel(Base):
    __tablename__ = "__users__"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    email_encrypted: Mapped[dict] = mapped_column(JSON)
    password_encrypted: Mapped[dict] = mapped_column(JSON)
```

### Column Type
By default, the column type for storing encrypted data must support serialization of the python `dict` type. If that is not possible, a custom serializer can be provided. In the example above, we're using `JSON` as the column type.

The data stored in encrypted field is a dictionary with the following keys:
- 'data': The encrypted data
- 'dek': The encrypted Data Encryption Key (DEK)


**Example Model Usage**
```python

# session = SQLAlchemy session
user = UserModel()
user.name = "John Doe"
user.email = "john@somewhere.com"
user.password = "password123"       # It's a secret to everyone!
session.add(user)
session.commit()
```

## Custom Transformer
If your database does not support storing python `dict` types, you can provide a custom transformer to the `@encrypt_fields` decorator. The transformer is a class implementing the `BaseTransformer` interface. The `BaseTransformer` interface has two methods: `serialize` and `deserialize`. The `serialize` method should take a python `dict` and return a serializable object. The `deserialize` method should take a serializable object and return a python `dict`.

**Example Custom Data Transformer**

Here's an example of storing the encrypted data on a `Text` column as a JSON string. The custom data transformer will convert the python `dict` to a JSON string and back.

```python
import json
from sqlalchemy_field_encryption import BaseTransformer

class CustomTransformer(BaseTransformer):
    """Convert a dict to a JSON string and back."""
    def serialize(self, data: dict) -> str:
        return json.dumps(data)

    def deserialize(self, data: str) -> dict:
        return json.loads(data)

@encrypt_fields(kek=SECRET_KEY, transformer=CustomTransformer)
class UserModel(Base):
    __tablename__ = "__users__"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    email_encrypted: Mapped[dict] = mapped_column(Text)
    password_encrypted: Mapped[dict] = mapped_column(Text)
```
