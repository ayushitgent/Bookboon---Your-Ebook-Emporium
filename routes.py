from flask import render_template, request, url_for, redirect, send_file
from flask_login import login_user, logout_user, current_user, login_required
from models import User, Section, Book, BookIssue
from flask_bcrypt import generate_password_hash, check_password_hash
import json
import ast
from datetime import datetime, timedelta
from sqlalchemy import or_

def register_routes(app, db):

    @app.route('/')
    def index():
        return render_template('login.html')

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == "GET":
            return render_template('signup.html')
        if request.method == "POST":
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')
            hashed_password = generate_password_hash(password=password)
            user = User.query.filter(User.username==username).first()
            if not user :
                user = User(username=username, password=hashed_password, role=role)
                db.session.add(user)
                db.session.commit()
                login_user(user)
            else:
                return render_template('signup.html', failure_message="User already exist")
            return redirect(url_for('index'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == "GET":
            return render_template('login.html')
        if request.method == "POST":
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter(User.username==username).first()
            if not user :
                return "Incorrect Username"
            elif not check_password_hash(user.password, password):
                return "Incorrect Password"
            else:
                login_user(user)
                if user.role == "Admin":
                    return redirect(url_for("sections"))
                else:
                    return redirect(url_for("get_books"))
    
    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for("index"))

    @app.route('/sections', methods=['GET','POST'])
    def sections():
        if request.method == "GET":
            title = request.args.get('title')
            error_message = request.args.get("error_message")
            if title:
                section = Section.query.filter(Section.title==title).first()  
                sections = Section.query.all()  
                context = { "sections": sections,
                            "section": section
                            }   
                return render_template('sections.html', **context)
            query = request.args.get('query')
            if query:
                sections = Section.query.filter(Section.title.like(f'%{query}%')).all()
                print(sections)
                context = { "sections": sections,
                           }                         
                return render_template('sections.html', **context)  
            sections = Section.query.all()  
            context = { "sections": sections,
                        "error_message" :error_message,
                       }                         
            return render_template('sections.html', **context)

        if request.method == "POST" and request.form.get('_method') == "PUT":
            section_id = request.form.get('section_id')
            section = Section.query.get(section_id)
            try:
                date_obj = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
            except ValueError:
                return "Incorrect date format. Please provide the date in the format YYYY-MM-DD."
            section.date = date_obj
            section.description = request.form.get('description')       
            db.session.commit()
            return redirect(url_for("sections"))

        if request.method == "POST" and request.form.get('_method') == "DELETE":
            section_id = request.form.get('section_id')
            section = Section.query.get(section_id)
            db.session.delete(section)
            db.session.commit()
            return redirect(url_for("sections"))

        if request.method == "POST":
            error_message = ""
            title = request.form.get('title')
            section = Section.query.filter(Section.title==title).first()

            if section :
                error_message = "Section Title Already Exist"
                return redirect(url_for("sections",error_message=error_message))

            try:
                date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
            except ValueError:
                error_message = "Incorrect date format. Please provide the date in the format YYYY-MM-DD."
                return redirect(url_for("sections",error_message=error_message))

            description = request.form.get('description')
            section = Section(title=title, date=date, description=description)
            db.session.add(section)
            db.session.commit()

            return redirect(url_for("sections",error_message=error_message))


    @app.route('/get_books', methods=['GET'])
    def get_books():
        if request.method == "GET":

            name = request.args.get('name')
            authors = request.args.get('authors')
            section_id = request.args.get('section_id')
            if name and authors and section_id:
                book_obj = Book.query.filter(Book.name==name).first()  
                authors_set = set(map(str.strip, authors.split(",")))
                authors_json = json.dumps(list(authors_set))
                book = Book.query.filter(Book.name==name, Book.authors==authors_json).first()
                section_obj = Section.query.get(section_id)
                book_objs = Book.query.filter_by(section=section_obj).all()
                book.authors = str(json.loads(book.authors))
                context = { "books": book_objs,
                            "book": book,
                            "section": section_obj
                            }   
                return render_template('section_books.html', **context)


            query_section_books = request.args.get('query_section_books')
            if query_section_books:

                category = request.args.get('category')

                if category == "title":
                    to_query = Book.name.like(f'%{query_section_books}%')
                else:
                    to_query = Book.authors.like(f'%{query_section_books}%')
                section_id = request.args.get('section_id')
                section_obj = Section.query.get(section_id)
                book_objs = Book.query.filter_by(section=section_obj).filter(to_query).all()
                context = {
                    "books": book_objs,
                    "section":section_obj,
                    }
                return render_template('section_books.html', **context)

            query_all_books = request.args.get('query_all_books')
            if query_all_books:
                category = request.args.get('category')

                if category == "title":
                    to_query = Book.name.like(f'%{query_all_books}%')
                elif category == "section":
                    to_query = Book.section_relationship.has(Section.title.like(f'%{query_all_books}%'))
                else:
                    to_query = Book.authors.like(f'%{query_all_books}%')

                book_objs = Book.query.filter(to_query).all()

                context = {
                    "books": book_objs,
                    }
                return render_template('all_books.html', **context)

            is_current_user= request.args.get('query_current_user')
            if is_current_user:
                user_book_issue_objs = BookIssue.query.filter(BookIssue.issued_to==current_user.username)
                context = {
                    "books_issued": user_book_issue_objs,
                    }
                return render_template('user_books.html', **context)

            is_admin= request.args.get('query_admin')
            if is_admin:
                admin_book_asked_objs = BookIssue.query.filter(
                    or_(BookIssue.issue_status == 1, BookIssue.issue_status == -1)).order_by(
                    BookIssue.issue_status).all()
                context = {
                    "books_asked": admin_book_asked_objs,
                    }
                return render_template('admin_books.html', **context)
            
            section_id = request.args.get('section_id')
            if section_id:
                section_obj = Section.query.get(section_id)
                book_objs = Book.query.filter_by(section=section_obj).all()
                for book in book_objs:
                    book.authors = str(json.loads(book.authors))
                context = {
                    "section":section_obj,
                    "books":book_objs
                    }
                return render_template('section_books.html', **context)
            

            book_objs = Book.query.order_by(Book.book_id.desc()).all()
            for book in book_objs:
                book.authors = str(json.loads(book.authors))
            context = {
                "books": book_objs,
            }
            return render_template('all_books.html', **context)

                


    @app.route('/add_books', methods=['POST'])
    def add_books():

        if request.method == "POST" and request.form.get('_method') == "PUT":
            # import ipdb; ipdb.set_trace();
            section_id = request.form.get('section_id')
            book_id = request.form.get('book_id')
            name = request.form.get('name')
            authors = request.form.get('authors')
            authors_json = json.dumps(ast.literal_eval(authors))
            content = request.form.get('content')
            no_of_pages = request.form.get('pages')
            price = request.form.get('price')

            book_obj = Book.query.filter(Book.name==name, Book.authors==authors_json).first()
            if not book_obj:
                return "No Such Combination of Books and Authors Exist"

            book_obj.content = content
            book_obj.no_of_pages = no_of_pages
            book_obj.price = price            
            db.session.commit()
            return redirect(url_for('get_books') + f'?section_id={section_id}')

        if request.method == "POST":
            section_id = request.form.get('section_id')
            name = request.form.get('name')
            authors = request.form.get('authors')
            authors_set = set(map(str.strip, authors.split(",")))
            authors_json = json.dumps(list(authors_set))
            content = request.form.get('content')
            no_of_pages = request.form.get('pages')
            price = request.form.get('price')

            book_objs = Book.query.filter(Book.name==name).all()
            if book_objs:
                for book_obj in book_objs:
                    existing_author_set = set(author for author in json.loads(book_obj.authors))
                    if existing_author_set == authors_set:
                        return "Combination of Books and Author Already Exist"

            new_book = Book(name=name, content=content, no_of_pages=no_of_pages, authors=authors_json, section_id=section_id, price=price)
            db.session.add(new_book)
            db.session.commit()
            return redirect(url_for('get_books') + f'?section_id={section_id}')

    @app.route('/view_content')
    def view_content():
        content = request.args.get('content')
        return render_template('view_content.html', content=content)

    @app.route('/delete_book', methods=['POST'])
    def delete_book():
        if request.method == "POST":
            book_id = request.form.get('book_id')
            section_id = request.form.get('section_id')

            if book_id:
                book_obj = Book.query.get(book_id)
                
                if book_obj:
                    db.session.delete(book_obj)
                    db.session.commit()

            return redirect(url_for('get_books') + f'?section_id={section_id}')
        

    
    @app.route('/request_book', methods=['GET', 'POST'])
    def request_book():

        if request.method == "GET":  
            book_id = int(request.args.get('book_id'))

            if book_id:
                book_issue_obj = BookIssue.query.filter_by(book_id=book_id).first()  
                issue_count = BookIssue.query.filter(BookIssue.issued_to==current_user.username,
                        or_(BookIssue.issue_status == 1, BookIssue.issue_status == -1)).count()


                if issue_count > 4:
                    return "You have exceeded the maximum limit(5 books) to request a book"

                if book_issue_obj:
                    if book_issue_obj.issue_status == 1:
                        if current_user == book_issue_obj.issued_to:
                            return "Already Issued to You."
                        else:
                            return f"Issued to Someone Else, it will be freed by {book_issue_obj.return_date}"
                    elif book_issue_obj.issue_status == -1:
                        return f"Already requested by Someone."
                    else:
                        BookIssue.query.filter_by(book_id=book_id).update({BookIssue.issue_status:-1, BookIssue.issued_to:current_user.username})
                        db.session.commit()
                else:
                    new_book_issue = BookIssue(issue_status=-1, issued_to=current_user.username, book_id=book_id)
                    db.session.add(new_book_issue)
                    db.session.commit()

            return redirect(url_for('get_books'))
    
        if request.method == "POST":  
            # import ipdb; ipdb.set_trace();
            book_id = int(request.form.get('book_id'))
            decision = request.form.get('decision')

            if decision == "revoke":
                issue_status = 0
                return_date = datetime.now().date()

                BookIssue.query.filter_by(book_id=book_id).update({BookIssue.issue_status: issue_status,
                                        BookIssue.return_date: return_date})
            elif decision == "decline":
                issue_status = 0
                BookIssue.query.filter_by(book_id=book_id).update({BookIssue.issue_status: issue_status})
            else:
                issue_status = 1
                issue_date = datetime.now().date()
                return_date = (datetime.now() + timedelta(days=7)).date()  # 7 days from now
                BookIssue.query.filter_by(book_id=book_id).update({BookIssue.issue_status: issue_status, BookIssue.issue_date: issue_date, BookIssue.return_date: return_date})

            db.session.commit()
            return redirect(url_for('get_books', query_admin=True))
    
    @app.route('/return_book', methods=['GET', 'POST'])
    def return_book():

        if request.method == "GET":  
            book_id = int(request.args.get('book_id'))

            if book_id:
                issue_status = 0
                return_date = datetime.now().date()
                BookIssue.query.filter_by(book_id=book_id).update({BookIssue.issue_status: issue_status,
                                        BookIssue.return_date: return_date})
        
        db.session.commit()
        return redirect(url_for('get_books', query_current_user=True)) 

    @app.route('/pay_and_download', methods=['POST'])
    def pay_and_download():
        if request.method == "POST":
            book_id = request.form.get('book_id')
            price = request.form.get('price')

            if book_id:
                book_obj = Book.query.get(book_id)
                
                if int(book_obj.price) == int(price):
                    content = book_obj.content
                    file_name = f"{book_obj.name}.txt"

                    with open(file_name, 'w') as file:
                        file.write(content)
                    return send_file(file_name, as_attachment=True)
                
                return "Please retry with same amount as Book Price"
                                     
    @app.route('/rate', methods=['POST'])
    def rate():
        if request.method == "POST":
            book_id = request.form.get('book_id')
            rating = request.form.get('rating')

            if not((isinstance(rating, str) and rating.isdigit()) or isinstance(rating, int)):
                return "Please enter a valid rating between 1 and 5"
            else:
                rating = int(rating)

            if int(rating) > 5 or int(rating) < 1:
                return "Please enter rating between 1 and 5"

            if book_id:
                book_obj = Book.query.get(book_id)
                if book_obj.rating == None and book_obj.no_of_people_rated == None:
                    book_obj.rating = 0
                    book_obj.no_of_people_rated = 0

                book_obj.rating = (book_obj.rating*book_obj.no_of_people_rated + rating)/(book_obj.no_of_people_rated +1)
                book_obj.no_of_people_rated += 1 
            
            db.session.commit()
            return redirect(url_for('get_books', query_current_user=True))
                    