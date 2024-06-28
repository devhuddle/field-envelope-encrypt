from typing import Any
from cryptography.fernet import Fernet

class BaseTransformer:
    """A class for creating custom serializers and deserializers."""
    def serizlize(self, data: dict) -> Any:
        ...

    def deserialize(self, data: Any) -> dict:
        ...


class EncryptedField:
    """
    A descriptor that creates a new field on the database class which users can interface with, ignoring the details of encryption and decryption.

    Encryption Design:
    - Each field will be encrypted with a unique Data Encryption Key (DEK) that is generated each time the field is set.
    - The DEK and value are both encrypted with the Key Encryption Key (KEK), which is stored in the environment.
    - The mk_type and mk_version fields are for future-proofing when we need to roll the key.
    """
    def __init__(self, name: str, kek: str, transfomer: BaseTransformer | None):
        self.name = name
        self.kek = kek
        self.dict_transformer = transfomer
        self.encrypted_name = f"{name}_encrypted"

    def __get__(self, obj, objtype=None):
        """Return the decrypted value of the field."""
        if obj is None:
            return self
        encrypted_value = getattr(obj, self.encrypted_name)
        if encrypted_value:
            if self.dict_transformer:
                dek = self.dict_transformer().deserialize(encrypted_value)['dek']
            else:
                dek = encrypted_value['dek']

            decoded_dek = Fernet(self.kek).decrypt(dek.encode()).decode()

            if self.dict_transformer:
                values = self.dict_transformer().deserialize(encrypted_value)
            else:
                values = encrypted_value

            return Fernet(decoded_dek).decrypt(values['value'].encode()).decode()

        return None

    def __set__(self, obj, value):
        """Encrypt the value and store it in the database."""
        # Generate a new Data Encryption Key (DEK)
        dek = Fernet.generate_key()

        # The data that will be set on the object
        encrypted_value = {
            'value': Fernet(dek).encrypt(value.encode()).decode(),
            'dek': Fernet(self.kek).encrypt(dek).decode()
        }

        # If there is a need to convert the dictionary into something else, call the serializer
        if self.dict_transformer:
            encrypted_value = self.dict_transformer().serialize(encrypted_value)

        # Store the new encrypted value as well as the encrypted DEK
        setattr(obj, self.encrypted_name, encrypted_value)


def _encrypt_fields(cls, kek: str, dict_transformer: Any | None = None):
    """
    A class decorator that provides encryption for fields that end in "_encrypted".

    Usage:
    Apply @encrypted to a class to enable encryption for fields that end in "_encrypted".
    Each ***_encrypted field MUST be a JSONB field (or something capable of accpting a Python dictionary type).
    When using the class, instead of referencing the ***_encrypted verion of the field, simply reference the base name.

    Example:
    @encrypted
    class User:
        id = Column(Integer, primary_key=True)
        email_encrypted = Column(JSONB)

    user = User()
    user.email = 'rob@devhuddle.ai'   # This will automatically be encrypted and stored in the email_encrypted field.
    ...

    user = session.query(User).first()
    print(user.email)  # This will automatically be decrypted from "user_encrypted" and returned as a string
    """

    fields = {}
    for name, attr in cls.__dict__.items():
        if name.endswith('_encrypted'):
            base_name = name[:-10]  # Remove '_encrypted' suffix
            fields[base_name] = EncryptedField(base_name, kek, dict_transformer)

    # NOTE: We're running this loop again to avoid modifying the dictionary while iterating over it
    for base_name, field in fields.items():
        setattr(cls, base_name, field)

    return cls

def encrypt_fields(kek: str, dict_transformer: BaseTransformer | None = None):
    """
    A decorator that provides encryption for fields that end in "_encrypted".

    Usage:
    Apply @encrypt_fields(kek) to a class to enable encryption for fields that end in "_encrypted".
    Each ***_encrypted field MUST be a JSONB field (or something capable of accpting a Python dictionary type).
    When using the class, instead of
    """
    def encrypted_fields_inner(cls):
        return _encrypt_fields(cls, kek=kek, dict_transformer=dict_transformer)

    return encrypted_fields_inner
