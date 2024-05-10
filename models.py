from app import db
from flask_login import UserMixin
from sqlalchemy import CheckConstraint, Numeric


class User(db.Model, UserMixin):
    __tablename__ = "users"

    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f'User: {self.username}, Role: {self.role}'

    def get_id(self):
        return self.uid


class Section(db.Model):
    __tablename__ = "sections"

    section_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String, nullable=True)

    section_books = db.relationship('Book', backref='section', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f'Section: {self.title}, desc: {self.description}'

    def get_id(self):
        return self.section_id

class Book(db.Model):
    __tablename__ = "books"  

    book_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    content = db.Column(db.Text, nullable=False)
    no_of_pages = db.Column(db.Integer, nullable=False)
    authors = db.Column(db.String, nullable=False)
    rating = db.Column(Numeric(precision=1, scale=2), nullable=True)
    no_of_people_rated = db.Column(db.Integer, nullable=True)
    price =  db.Column(db.Integer, nullable=False)

    section_id = db.Column(db.Integer, db.ForeignKey('sections.section_id', ondelete='CASCADE'), nullable=False)
    section_relationship = db.relationship('Section', backref=db.backref('books', lazy=True))

    # Define the one-to-one relationship with BookIssue
    book_issue = db.relationship('BookIssue', back_populates='book', uselist=False)

    def __repr__(self):
        return f'Book: {self.name}, content: {self.content}'

    def get_id(self):
        return self.book_id

class BookIssue(db.Model):
    __tablename__ = "book_issue"  

    book_issue_id = db.Column(db.Integer, primary_key=True)
    issue_status = db.Column(db.Integer, nullable=False)#1-Issue Accepted, 0-Issue Rejected/Not Asked by Anyone, -1-Pending
    issued_to = db.Column(db.String, nullable=True)
    issue_date = db.Column(db.Date, nullable=True)
    return_date = db.Column(db.Date, nullable=True)

    __table_args__ = (
        CheckConstraint('issue_status IN (1, 0, -1)', name='issue_status_check'),
    )

    # Define the back reference to Book
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'), unique=True)
    book = db.relationship('Book', back_populates='book_issue')

    def __repr__(self):
        return f'Book Issue ID: {self.book_issue_id}, Issue Status: {self.issue_status}'

    def get_id(self):
        return self.book_issue_id
