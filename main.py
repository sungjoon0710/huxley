from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from pymongo import MongoClient
import certifi
from pydantic import BaseModel
import openai
import time
from fastapi.middleware.cors import CORSMiddleware




openai.api_key = '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'

class user(BaseModel):
    userid: str
    userpw: str
    userexp: int

class Plan:
    def __init__(self,destination_input: str, destination_time: str, travel_style: str ):
        self.destination_input = destination_input
        self.destination_time = destination_time
        self.travel_style = travel_style

class Log:
    def __init__(self, destination_input: str, log_start_date: str, log_end_date: str, log_experience: str):
        self.destination_input = destination_input
        self.log_start_date = log_start_date
        self.log_end_date = log_start_date
        self.log_experience = log_experience

        
        


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/resources", StaticFiles(directory="static/resources"), name="favicon")
app.mount("/static", StaticFiles(directory="static"), name="static")
# 이를 통해  css 스타일시트를 불러온다


url ="mongodb+srv://sungjoon0710:0R41dhrwNj8cOTsY@cluster0.hplaa84.mongodb.net/?retryWrites=true&w=majority"
ca = certifi.where()
client = MongoClient(url, tlsCAFile=ca)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)



print(client)
print("\n")

database = client['sungjoons']
print(f"database {database} obtained \n")

collection = database['user']
print(f"collection user obtained. \n")

collection2 = database['itin']
print(f"collection 2 itin obtained. \n")

collection3 = database['logs']
print(f"collection 3 logs obtained. \n")

collection4 = database['sessions']
print(f"collection 4 sessions obtained. \n")


##CHATGPT TERRITORY#####
# mongo_client = AsyncIOMotorClient("mongodb://localhost:27017")
# mongo_db = mongo_client["your_database_name"]
# users_collection = mongo_db["user"]  # Modified collection name
# session_collection = mongo_db["sessions"]
# app.add_middleware(SessionMiddleware, secret_key="your_secret_key", backend=MongoDBBackend(session_collection))


# user_find ={"userid" : "sungjoon"}
# result = collection.find_one(user_find)
# print(f"success finding user{result}")
##CHATGPT TERRITORY#####



#FastAPI Methods Implementation
@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request" : request, "title": "Main Page of Huxley"})
@app.get("/index")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request" : request, "title": "Main Page of Huxley"})


@app.get("/travel-log")
async def read_travelog(request: Request):
    return templates.TemplateResponse("travel-log.html", {"request": request, "title": "Travel Logbook"})

@app.post("/travel-log")
async def add_log(request: Request, destination_input: str = Form(...), log_start_date: str = Form(...), log_end_date: str = Form(...), log_experience: str = Form(...)):
    
    #Create a user document
    new_log = Log(destination_input, log_start_date, log_end_date, log_experience)


    new_log_dict = {"destination_input" : destination_input, "log_start_date" : log_start_date, "log_end_date" : log_end_date, "log_experience" : log_experience}
    # Insert the log document into the MongoDB collection log
    
    
    collection3.insert_one(new_log_dict)
    print("log addition successful")
    
    return templates.TemplateResponse("travel-loginfo.html", {"request": request, "new_log": new_log})



@app.get("/mapbox-destination")
async def read_destination(request: Request):
    return templates.TemplateResponse("mapbox-destination.html", {"request": request, "title": "Destination"})

@app.get("/privacy-policy")
async def read_privacy(request: Request):
    return templates.TemplateResponse("privacy-policy.html", {"request": request, "title": "Your Privacy"})


@app.get("/register")
async def register_form(request: Request):
     return templates.TemplateResponse("register.html", {"request": request})

#Implementation of Signup through Register
@app.post("/register")
async def add_user(request: Request, userid: str = Form(...), userpw: str = Form(...), userexp: int = Form(...) ):
    
    #Create a user document
    new_user = {"userid" : userid, "userpw" : userpw, "userexp": userexp}
    
    # Insert the user document into the MongoDB collection
    result = collection.insert_one(new_user)
    # Return the inserted user's ID or other response
    return templates.TemplateResponse("registerinfo.html", {"request": request, "userid": userid, "userpw": userpw, "userexp": userexp})


#Implementation of Login
@app.get("/login")
async def login_form(request: Request):
     return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, userid: str = Form(...), userpw: str = Form(...)):
    

    
    
    user = collection.find_one({"userid": userid})
    
    try:
        if user:
            trueuserpw = user.get("userpw")
            if userpw == trueuserpw:
                # session["userid"] = userid  
                # return RedirectResponse(url="/dashboard")
                return templates.TemplateResponse("logininfo.html", {"request": request, "userid": userid, "userpw": userpw})
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except:
        print("Error finding user, please try again.")
        return templates.TemplateResponse("workaround-loginfail.html", {"request": request})
        #this is a temporary workaround. once learning JS, implement a popup and redirect to login
        #return templates.TemplateResponse("login.html", {"request": request, "title": "Login"})
    




class ItinGenerator:
    def __init__(self, engine = 'gpt-3.5-turbo'):
        self.engine = engine 
        self.type = self.get_type_engine(engine)
        #type에 chat이 저장된다.

    def get_type_engine(self,engine):
        if engine.startswith('gpt-3.5'):
            return 'chat'
        elif engine.startswith('text-'):
            return 'text'
        raise Exception(f'unknown model: {engine}')
    

    def generate(self, destination_input, destination_time, travel_style):
        prompt = f'Please suggest a {destination_time}-long itinerary in {destination_input} for someone whose travel style is of the {travel_style} style. Please do not add any greetings in the beginning.'
        

        if self.type == 'chat':
            result = self.using_chatgpt(prompt = prompt)
            #함수의 (prompt = )에다가 prompt를 넣는것
        return result
    
    def using_chatgpt(self, prompt):
        system_instruction = "Assistant is a local living in the area recommending things to do in the city and in the vicinity."
        messages = [{'role': 'system', 'content': system_instruction},{'role':'user', 'content':prompt}]
        response = openai.chat.completions.create(
            model = self.engine, messages = messages
        )
        result = response.choices[0].message.content.strip()
        return result

@app.get("/itinerary-planner")
async def itin_planner(request: Request):
    return templates.TemplateResponse("itinerary-planner.html", {"request": request})

@app.post('/itinerary-planner')
async def generate_itinerary(request: Request, destination_input: str = Form(...), destination_time: str = Form(...), travel_style: str = Form(...)):
    #comes into the post method in JSON format from the streamlit file, as defined by basemodel above
    
    #we need a Plan!
    plan = Plan(destination_input, destination_time, travel_style)
    

    itinGenerator = ItinGenerator()
    itin = itinGenerator.generate(destination_input= plan.destination_input, destination_time= plan.destination_time, travel_style= plan.travel_style)
    
    print(itin)

    
    new_itin_parsed = await itin_parser(itin)
    # collection2.insert_one(new_itin_parsed)
    print(new_itin_parsed)

    new_itin = {"destination_input" : destination_input, "destination_time" : destination_time, "travel_style" : travel_style, "itin" : new_itin_parsed}
    

    collection2.insert_one(new_itin)
    print("success saving itinerary")

    return templates.TemplateResponse("itineraryinfo.html", {"request": request, "new_itin": new_itin})
    # return templates.TemplateResponse("itineraryinfo.html", {"request": request, "destination_input" : destination_input, "itin": itin})
    


async def itin_parser(itin: str):
    itin_split = itin.split("Day")
    itin_dict = {}
    

    for num, name in enumerate(itin_split, start =0):
        print("Day{}".format(name))
        itin_dict["day_{}".format(num)]= "Day{}".format(name)

    itin_dict.pop('day_0')
    
    return itin_dict



# class Item(BaseModel):  # Pydantic model to structure data
#     name: str
#     description: str

@app.get("/itin_from_mongo", response_model = dict)
async def read_itin_from_mongo(destination_input: str):
    
    sample_itin = {"destination_input" :destination_input, "destination_time": "none", "itin": "none", "travel_style" : "none"}

    if collection2.find_one({"destination_input": destination_input},{"_id": 0}):

        itin_from_mongo = collection2.find_one({"destination_input": destination_input},{"_id": 0})  
        return itin_from_mongo
        # Fetch data from MongoDB
    return sample_itin;

