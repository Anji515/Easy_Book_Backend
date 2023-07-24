from mongoengine import connect , Document, StringField, ReferenceField, IntField, ListField ,DateField

connect('Easy_Book_App', host='mongodb+srv://anji:kommu@cluster0.dxyi0uo.mongodb.net/?retryWrites=true&w=majority')

class Movie(Document):
    title = StringField(required=True)
    description = StringField()
    duration = IntField()
    genre = StringField()
    language = StringField()
    release_date = DateField()
    image_cover = StringField()
    rating = IntField()

class Theater(Document):
    name = StringField(required=True)
    address = StringField()
    city = StringField()
    state = StringField()
    capacity = IntField()

class Show(Document):
    movie_id = ReferenceField(Movie, required=True)
    theater_id = ReferenceField(Theater, required=True)
    show_timing = ListField(StringField())
    category =  ListField(StringField())
    dates = ListField(StringField())
