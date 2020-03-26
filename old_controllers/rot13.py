import webapp2
import cgi


form="""
<h2>Enter some text to RTO13:</h2>
<form method="post">
    <textarea name="text" rows="8" cols="60">%(toform)s</textarea>
    <br>
    <input type="submit" value="Submit">
</form>
"""


#function to generate a rotX dictionary
def rotX(X):
    rot_dic={}
    for i in range(65,90+1):
        if i+X<=90:
            rot_dic.setdefault(i,i+X)
        else:
            rot_dic.setdefault(i,i-(90-65)+X-1)
    for i in range(97,122+1):
        if i+X<=122:
            rot_dic.setdefault(i,i+X)
        else:
            rot_dic.setdefault(i,i-(122-97)+X-1)
    return rot_dic 
        
        
rot_dic=rotX(13) 


class MainPage(webapp2.RequestHandler):
    
    
    #compute the ascii equivalente and subtite using dictionary
    def rottext(self,usertext,rot_dic):
        rottext=""
        for aux in usertext:
            auxascii=ord(aux)
            if (auxascii>=65 and auxascii<=90) or (auxascii>=97 and auxascii<=122) :
                auxascii=rot_dic.get(auxascii)
            
            rottext=rottext+chr(auxascii)
        return cgi.escape(rottext,quote=True)
      
    
    def write_form(self,toform=""):
        self.response.out.write(form % {"toform":toform})
    def get(self):
        ##generating the rot13 dic
        
        self.write_form()
        
    def post(self):
        usertext=self.request.get("text")
         
        self.write_form(self.rottext(usertext,rot_dic))
        
        
        
    
app=webapp2.WSGIApplication([('/', MainPage)],debug=True)