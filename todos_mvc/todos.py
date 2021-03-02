from flask import Blueprint
from flask import Flask
from flask import flash
from flask import render_template
from flask import request, redirect, url_for
from werkzeug.utils import secure_filename
from base64 import b64encode


from todos_mvc.model import Todo, db

bp = Blueprint('todos', __name__)


@bp.route('/')
def hello_world():
    return 'Hello, Todos App!'


@bp.route('/todos', methods=['GET'])
def home():
    rs = Todo.query.all()
    todo_list = []
    for todo in rs:
        t = {
            'id': todo.id,
            'title': todo.title,
            'complete': todo.complete,
        }

        try:
            t['img'] = b64encode(todo.pic).decode("utf-8")
        except Exception as e:
            print('>> error decoding image', e)

        todo_list.append(t)

    # transform blob to base64 for img tag data:uri
    # todo_list = [
    #     {
    #         'id': todo.id,
    #         'title': todo.title,
    #         'complete': todo.complete,
    #         'img': b64encode(todo.pic).decode("utf-8")
    #     } for todo in Todo.query.all()
    # ]
    return render_template('todos/home.html', todo_list=todo_list)


@bp.route('/todos/add', methods=['POST'])
def add():
    title = request.form.get('title')

    file_err = None
    if 'pic' not in request.files:
        print('>> no file uploaded')
        flash('no file uploaded')
    else:
        file = request.files['pic']

        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('no file selected for upload')
            print('>> no file selected for upload')
        filename = secure_filename(file.filename)

        # check file is not as easy
        file_err = None
        # first try check browser content length if given
        if file.content_length:
            print('>> file content_length: ', file.content_length)
            if file.content_length > 1000000:
                file_err = 'file size is too large: ' + file.content_length
        else:
            # use seek and tell methods to get size without loading content
            # into memory
            pos = file.tell()
            file.seek(0, 2)  # seek to end
            size = file.tell()
            file.seek(pos)  # back to original position
            print('>> file size by seeking: ', size)
            if size > 1000000:
                # size_err = f'file size is too large: {size}'
                file_err = 'file size is too large'

    new_todo = Todo(title=title, complete=False)

    if file_err:
        flash(file_err)
        print(file_err)
    else:
        blob = file.read()
        # todo: be careful not to read too much data into memory
        # this is not considerred safe to be used for size check
        # size = len(blob)
        new_todo.pic = blob

    db.session.add(new_todo)
    db.session.commit()
    return redirect(url_for('home'))


@bp.route('/todos/update/<todo_id>', methods=['POST', 'PUT'])
def update(todo_id):
    try:
        todo = Todo.query.filter_by(id=todo_id).first()
        new_title = request.form.get('title')
        new_complete = bool(request.form.get('complete'))
        if todo:
            todo.title = new_title
            todo.complete = new_complete
            db.session.commit()
    except Exception as e:
        print('Failed to update todo:', todo)
        print(e)
    return redirect('/todos')


# @bp.route('/todos/delete/<int:todo_id>')
@bp.route('/todos/delete/<todo_id>', methods=['POST', 'DELETE'])
def delete(todo_id):
    todo = Todo.query.filter_by(id=todo_id).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('home'))