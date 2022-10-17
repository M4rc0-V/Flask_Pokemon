from unicodedata import category
from app import db, login
from flask_login import UserMixin #### THIS IS ONLY FOR THE USER MODEL!!!!
from datetime import datetime as dt, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import secrets





followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    email = db.Column(db.String, unique=True, index=True)
    password = db.Column(db.String)
    created_on = db.Column(db.DateTime, default=dt.utcnow)
    icon = db.Column(db.Integer)
    token = db.Column(db.String, unique=True, index=True)
    token_exp = db.Column(db.DateTime)
    is_admin = db.Column(db.Boolean, default=False)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    followed = db.relationship('User', secondary=followers, 
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref = db.backref('followers', lazy="dynamic"),
        lazy = 'dynamic'
    )
    # current_user.followed.all() #all the people current user is following
    # current_user.followers.all() # all the people following the current user

    ##################################################
    ############## Methods for Token auth ############
    ##################################################    
    def get_token(self, exp=86400):
        current_time = dt.utcnow()
        # If their is a token and it is valid we willtreturn the token
        if self.token and self.token_exp > current_time+timedelta(seconds=60):
            return self.token
        # There was no token or It was expired, so make a new token
        self.token = secrets.token_urlsafe(32)
        self.token_exp = current_time + timedelta(seconds=exp)
        self.save()
        return self.token

    def revoke_token(self):
        self.token_exp = dt.utcnow() - timedelta(seconds=60)
    
    @staticmethod
    def check_token(token):
        # u=User.query.filter(User.token == token).first()
        u = User.query.filter_by(token = token).first()
        if not u or u.token_exp < dt.utcnow():
            return None
        return u



    #########################################
    ############# End Methods for tokens ####
    #########################################

    # Should return a unique identifing string
    def __repr__(self):
        return f'<User: {self.email} | {self.id} >'

    # Human Readable repr
    def __str__(self):
        return f'<User: {self.email} | {self.first_name} {self.last_name}>'
    
    # salt and hash our password to make it hard to steal
    def hash_password(self, original_password):
        return generate_password_hash(original_password)

    def check_hashed_password(self, login_password):
        return check_password_hash(self.password, login_password)

    # save the user to the db
    def save(self):
        db.session.add(self) # add the user to out session
        db.session.commit() # saves the session to the database

    def to_dict(self):
        return {
            'id':self.id,
            'first_name':self.first_name,
            'last_name':self.last_name,
            'email':self.email,
            'created_on' :self.created_on,
            'icon':self.icon,
            'token':self.token,
            'is_admin':self.is_admin
        }

    def from_dict(self, data):
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        self.email= data['email']
        self.password = self.hash_password(data['password'])
        self.icon = data['icon']

    def get_icon_url(self):
        return f"https://avatars.dicebear.com/api/adventurer/{self.icon}.svg"

    # Check to see if the user is following another user
    def is_following(self, user_to_check):
        # return user_to_check in self.followed
        return self.followed.filter(followers.c.followed_id == user_to_check.id).count()>0

    #Follow a User
    def follow(self, user_to_follow):
        if not self.is_following(user_to_follow):
            self.followed.append(user_to_follow)
            db.session.commit()
    
    #Unfollow a User
    def unfollow(self, user_to_unfollow):
        if self.is_following(user_to_unfollow):
            self.followed.remove(user_to_unfollow)
            db.session.commit()

    # Get all the posts for the users I am following and my own posts
    def followed_posts(self):
        # Get all the posts for the users I am following
        followed = Post.query.join(followers, (Post.user_id == followers.c.followed_id)).filter(followers.c.follower_id == self.id)
        # get all my posts
        # self_posts = self.posts <-- this works and is easy
        self_posts = Post.query.filter_by(user_id = self.id)
        # Smoooshhhh together and and sort by date newest first
        all_posts = followed.union(self_posts).order_by(Post.created_on.desc())
        return all_posts

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Post(db.Model):
    __tablename__ = 'post'

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    created_on = db.Column(db.DateTime, default=dt.utcnow)
    date_modified = db.Column(db.DateTime, onupdate=dt.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<Post: {self.id} | {self.body[:15]}>'

    def edit(self, new_body):
        self.body=new_body

    def to_dict(self):
        return{
            'id':self.id,
            'body':self.body,
            'created_on':self.created_on,
            'date_modified':self.date_modified,
            'user_id':self.user_id,
        }

    # save the post to the db
    def save(self):
        db.session.add(self) # add the post to out session
        db.session.commit() # saves the session to the database
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    products = db.relationship('Item', backref="cat", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        f'<Category: {self.id} | {self.name}>'

    # save the post to the db
    def save(self):
        db.session.add(self) # add the post to out session
        db.session.commit() # saves the session to the database
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def to_dict(self):
        return {
            "id":self.id,
            "name":self.name
        }



class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    desc = db.Column(db.Text)
    price = db.Column(db.Float)
    img = db.Column(db.String)
    created_on = db.Column(db.DateTime, default=dt.utcnow)
    category_id = db.Column(db.ForeignKey('category.id'))

    def __repr__(self):
        f'<Item: {self.id} | {self.name}>'

    # save the post to the db
    def save(self):
        db.session.add(self) # add the post to out session
        db.session.commit() # saves the session to the database
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    def to_dict(self):
        return {
            "id":self.id,
            "name":self.name,
            "desc":self.desc,
            "price":self.price,
            "img":self.img,
            "created_on":self.created_on,
            "category_id":self.category_id,
            "category_name":self.cat.name
        }

    def from_dict(self, data):
        for field in ["name", "desc", "price", "img", "category_id"]:
            if field in data:
                setattr(self, field, data[field])