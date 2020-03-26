import webapp2
import cgi

form="""
<form method="post">
    What is your birthday?
    <br>
    <label>Day<input type="text" name="day" value=%(dday)s></label>
    <label>Month <input type="text" name="month" value=%(dmonth)s></label>
    <label>Year <input type="text" name="year" value=%(dyear)s></label>
    <br>
    <div style="color:red"> %(error)s</div>
    <br>
    <input type="submit" value="Submit">
</form>
"""

monthdic = {'January': ('jan','1'),
            'February': ('feb','2'),
            'March': ('mar','3'),
            'April': ('apr','4'),
            'May': ('may','5'),
            'June': ('June','6'),
            'July': ('jul','7'),
            'August': ('aug','8'),
            'September': ('sep','9'),
            'October': ('oct','10'),
            'November': ('nov','11'),
            'December': ('dec','12'),}

def valid_month(month):
    for name, short in monthdic.iteritems():
        if short[0]==month[:3].lower()  or short[1]==month:
            return name
def valid_day(day):
    if day.isdigit():   
        day=int(day)
        if day>=1 and day<=31:
            return day
def valid_year(year):
    if year.isdigit():
        year=int(year)
        if year>=1900 and year<=2020:
            return year
def escape_html(str):
    return cgi.escape(str,quote=True)

class MainPage(webapp2.RequestHandler):
    def write_from(self,error="",dday="",dmonth="",dyear=""):
        self.response.out.write(form % {"error":error,
                                        "dday":escape_html(dday), 
                                        "dmonth":escape_html(dmonth),
                                        "dyear":escape_html(dyear)})
        
    def get(self):
        self.write_from()
        
    def post(self):
        user_day=self.request.get("day")
        user_month=self.request.get("month")
        user_year=self.request.get("year")
        
        day=valid_day(user_day)
        month=valid_month(user_month)
        year=valid_year(user_year)
                
        
        if not (day and month and year):
            self.write_from("That doesn't look valid to me, friend.",user_day,user_month,user_year)
        else:
            self.redirect("/thanks")
            
class ThanksHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write("<h2>Thanks! Date Validated.</h2>")
        
        
        
app = webapp2.WSGIApplication([('/', MainPage),('/thanks',ThanksHandler)])

