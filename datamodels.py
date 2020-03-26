from google.appengine.ext import db


class Users(db.Model):
    username=db.StringProperty(required=True)
    password=db.StringProperty(required=True)
    created=db.DateTimeProperty(auto_now_add=True)
    email=db.EmailProperty()
    
    
class WikiPages(db.Model):
    created=db.DateTimeProperty(auto_now_add=True)
    pageurl=db.StringProperty(required=True)
    pagecontent=db.TextProperty()
    



