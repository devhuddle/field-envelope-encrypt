import json
import pytest
from field_envelope_encrypt import encrypt_fields, BaseTransformer
from typing import Any

from cryptography.fernet import Fernet

from sqlalchemy import JSON, String, Text, Integer, create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Generate a Key Encryption Key (KEK) to use for tests
test_kek = Fernet.generate_key()

class Base(DeclarativeBase):
    ...


@pytest.fixture(scope="class")  # Use 'class' scope for one-time setup/teardown per test class
def engine():
    """
    Fixture to create a temporary in-memory SQLite engine.
    """
    engine = create_engine('sqlite:///:memory:')
    yield engine  # Yield the engine for test cases
    engine.dispose()  # Cleanup after all tests in the class


@pytest.fixture(scope="function")  # Use 'function' scope for a new session per test
def session(engine):
    """
    Fixture to create a database session per test case.
    """
    Base = declarative_base()

    # Crappy hack to get the UserModel to be created in the same scope as the tests
    # NOTE: This must match the UserModel class below
    class UserModel(Base):
        __tablename__ = "__users__"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        name: Mapped[str] = mapped_column(String(30))
        email_encrypted: Mapped[dict] = mapped_column(JSON)
        password_encrypted: Mapped[dict] = mapped_column(JSON)

    class UserModelWithTransform(Base):
        __tablename__ = "__users_str__"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        name: Mapped[str] = mapped_column(String(30))
        email_encrypted: Mapped[str] = mapped_column(Text)
        password_encrypted: Mapped[str] = mapped_column(Text)

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session  # Yield the session for the test

    session.close()  # Cleanup after each test


@encrypt_fields(kek=test_kek)
class UserModel(Base):
    __tablename__ = "__users__"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    email_encrypted: Mapped[dict] = mapped_column(JSON)
    password_encrypted: Mapped[dict] = mapped_column(JSON)

class Transformer(BaseTransformer):
    def serialize(self, data: dict) -> str:
        return json.dumps(data)

    def deserialize(self, data: Any) -> dict:
        return json.loads(data)

@encrypt_fields(kek=test_kek, dict_transformer=Transformer)
class UserModelWithTransform(Base):
    __tablename__ = "__users_str__"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    email_encrypted: Mapped[dict] = mapped_column(Text)
    password_encrypted: Mapped[dict] = mapped_column(Text)

class TestDecorator:

    def test_encrypted_fields(self, session):
        """Make sure that fields marked for encryption are encrypted."""
        user = UserModel()
        user.name = name = 'Code Monkey'
        user.email = email = 'test@code-a-lot.com'
        user.password = password = 'password123'

        # Make sure the fields are encrypted
        assert user.email_encrypted != user.email
        assert user.password_encrypted != user.password

        # Make sure the fields are decryptable and equal what they should
        assert user.name == name
        assert user.email == email

        # Make sure the encryptedf fields are decryptable and equal what they should
        assert user.email == email
        assert user.password == password

    def test_unencrypted_fields(self, session):
        """Make sure that fields that are not marked for encryption - are not encrypted."""
        user = UserModel()
        user.name = 'Code Monkey'

        assert user.name == 'Code Monkey'

        # Double check that the encrypted fields are not present
        assert hasattr(user, 'name_encrypted') == False

    def test_dict_transformer(self, session):
        """Ensure that the dictionary transformer is working properly."""
        user = UserModelWithTransform()
        user.name = name = 'Code Monkey'
        user.email = email = 'test@code-a-lot.com'
        user.password = password = 'password123'

        # Save off the original encrypted fields for verification later
        # NOTE: the encrypted fields are stored as strings
        encrypted_email = json.loads(user.email_encrypted)['value']
        encrypted_password = json.loads(user.password_encrypted)['value']

        # Persist the user to the database
        session.add(user)
        session.commit()

        # Query the database and see if the fields are still encrypted
        user = session.query(UserModelWithTransform).first()

        assert user.name == name
        assert user.email == email
        assert user.password == password

        # Make sure that the encrypted fields are still encrypted
        assert user.email_encrypted != email
        assert user.password_encrypted != password

        # Make sure the encrypted fields are the same as the original encrypted fields
        assert json.loads(user.email_encrypted)['value'] == encrypted_email
        assert json.loads(user.password_encrypted)['value'] == encrypted_password

    def test_database_persistence(self, session):
        """Verify that the encrypted fields are persisted to the database."""
        user = UserModel()
        user.name = name = 'Code Monkey'
        user.email = email = 'test@code-a-lot.com'
        user.password = password = 'password123'

        # Save off the original encrypted fields for verification later
        encrypted_email = user.email_encrypted['value']
        encrypted_password = user.password_encrypted['value']

        # Persist the user to the database
        session.add(user)
        session.commit()

        # Query the database and see if the fields are still encrypted
        user = session.query(UserModel).first()

        assert user.name == name
        assert user.email == email
        assert user.password == password

        # Make sure that the encrypted fields are still encrypted
        assert user.email_encrypted != email
        assert user.password_encrypted != password

        # Make sure the encrypted fields are the same as the original encrypted fields
        assert user.email_encrypted['value'] == encrypted_email
        assert user.password_encrypted['value'] == encrypted_password
