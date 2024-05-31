import graphene
import json
from flask import Flask
from flask_graphql import GraphQLView
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3308/perpustakaan'
db = SQLAlchemy(app)

# Model untuk tabel buku
class BookModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)

# GraphQL Type untuk buku
class Book(graphene.ObjectType):
    id = graphene.ID()
    title = graphene.String()

# Query resolver
class Query(graphene.ObjectType):
    book_by_id = graphene.Field(Book, id=graphene.Int())
    book_by_title = graphene.Field(Book, title=graphene.String())
    books = graphene.List(Book)

    def resolve_book_by_id(self, info, id):
        book = BookModel.query.get(id)
        if not book:
            raise ValueError("Buku dengan id tersebut tidak ditemukan.")
        return book
    
    def resolve_book_by_title(self, info, title):
        book = BookModel.query.filter_by(title=title).first()
        if not book:
            raise ValueError("Buku dengan judul tersebut tidak ditemukan")
        return book

    def resolve_books(self, info):
        return BookModel.query.all()

# Input untuk buku
class BookInput(graphene.InputObjectType):
    title = graphene.String(required=True)

# Mutation untuk membuat buku baru
class CreateBook(graphene.Mutation):
    class Arguments:
        book = BookInput(required=True)

    book = graphene.Field(Book)
    message = graphene.String()

    def mutate(self, info, book):
        existing_book = BookModel.query.filter_by(title=book.title).first()
        if existing_book:
            return CreateBook(message="Buku dengan judul tersebut sudah ada dalam database")

        new_book = BookModel(title=book.title)
        db.session.add(new_book)
        db.session.commit()

        return CreateBook(book=new_book, message="Buku berhasil ditambahkan.")

# Mutasi untuk mengupdate buku
class UpdateBook(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        book = BookInput(required=True)

    book = graphene.Field(Book)
    message = graphene.String()

    def mutate(self, info, id, book):
        book_to_update = BookModel.query.get(id)
        if not book_to_update:
            return UpdateBook(message="Buku tidak ditemukan")

        book_to_update.title = book.title
        db.session.commit()

        return UpdateBook(book=book_to_update, message="Buku berhasil diupdate.")

# Mutasi untuk menghapus buku
class DeleteBook(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    book_id = graphene.ID()
    message = graphene.String()

    def mutate(self, info, id):
        book_to_delete = BookModel.query.get(id)
        if not book_to_delete:
            return DeleteBook(message="Gagal Menghapus, Buku Tidak Ditemukan!")

        db.session.delete(book_to_delete)
        db.session.commit()

        return DeleteBook(message="Buku berhasil dihapus", book_id=id)

# Menambahkan mutasi baru ke dalam resolvers
class Mutation(graphene.ObjectType):
    create_book = CreateBook.Field()
    update_book = UpdateBook.Field()
    delete_book = DeleteBook.Field()


# Menambahkan schema GraphQL
schema = graphene.Schema(query=Query, mutation=Mutation)

# Endpoint GraphQL
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

if __name__ == '__main__':
    app.run(debug=True)
