from django.test import TestCase
from SECAAlgo.models import Images, Sessions, Annotations, Notes
from UserSECA.models import SECAUser
from django.contrib.auth.models import User


class SimpleImagePropertyTests(TestCase):
    exampleName = "name"
    real_image = "realRoom"
    predicted_image = "predictedRoom"

    def test_image_constructor(self):
        exampleName = "name"
        real_image = "realRoom"
        predicted_image = "predictedRoom"

        image = Images(image_name=exampleName, actual_image=real_image, predicted_image=predicted_image)
        self.assertEquals(image.image_name, exampleName)
        self.assertEquals(image.actual_image, real_image)
        self.assertEquals(image.predicted_image, predicted_image)

    def test_image_setter(self):
        exampleName = "name"
        real_image = "realRoom"
        predicted_image = "predictedRoom"
        exampleName2 = "Newname"
        real_image2 = "Another realRoom"
        predicted_image2 = "Newly predictedRoom"

        image = Images(image_name=exampleName, actual_image=real_image, predicted_image=predicted_image)

        self.assertEquals(image.image_name, exampleName)
        self.assertEquals(image.actual_image, real_image)
        self.assertEquals(image.predicted_image, predicted_image)

        image.image_name = exampleName2
        image.actual_image = real_image2
        image.predicted_image = predicted_image2

        self.assertEquals(image.image_name, exampleName2)
        self.assertEquals(image.actual_image, real_image2)
        self.assertEquals(image.predicted_image, predicted_image2)


class SimpleAnnotationPropertyTests(TestCase):

    def test_Annotation_constructor(self):
        exampleName = "name"
        real_image = "realRoom"
        predicted_image = "predictedRoom"

        image = Images(image_name=exampleName, actual_image=real_image, predicted_image=predicted_image)
        image.save()

        annotation_annotation = "This image is an image"
        bounding_box = "[20.0, 102931209]"
        weight = 42
        reason = "because the image is indeed an image"

        annotation = Annotations(image=image, annotation=annotation_annotation, bounding_box_coordinates=bounding_box,
                                 weight=weight, reason=reason)

        self.assertEquals(annotation.image, image)
        self.assertEquals(annotation.image.actual_image, real_image)
        self.assertEquals(annotation.annotation, annotation_annotation)
        self.assertEquals(annotation.bounding_box_coordinates, bounding_box)
        self.assertEquals(annotation.weight, weight)
        self.assertEquals(annotation.reason, reason)


class SimpleSessionsPropertyTests(TestCase):
    def test_session_constructor(self):
        exampleName = "name"
        real_image = "realRoom"
        predicted_image = "predictedRoom"
        image = Images(image_name=exampleName, actual_image=real_image, predicted_image=predicted_image)
        image.save()

        image2 = Images(image_name="name2", actual_image=real_image, predicted_image=predicted_image)
        image2.save()

        userName = "name"
        userPwrd = "securePassword"
        exampleUser = User(username=userName, password=userPwrd)
        exampleUser.save()
        secaUser = SECAUser(user=exampleUser, is_developer=False, notes="some note here")
        secaUser.save()

        session = Sessions(name="session_1")
        session.save()
        session.images.add(image)
        session.images.add(image2)
        session.users.add(secaUser)

        self.assertEquals(session.images.all()[0], image)
        self.assertEquals(session.images.all()[1], image2)
        self.assertEquals(session.images.all().count(), 2)
        self.assertEquals(session.users.all()[0], secaUser)
        self.assertEquals(session.users.all().count(), 1)
        self.assertEquals(session.name, "session_1")


class SimpleNoteTests(TestCase):
    def test_Notes_constructor(self):
        userName = "name"
        userPwrd = "securePassword"
        exampleUser = User(username=userName, password=userPwrd)
        exampleUser.save()

        isSecaUserDeveloper = False
        secaUserPersonalNotes = "this note is different apparently"
        secaUser = SECAUser(user=exampleUser, is_developer=isSecaUserDeveloper, notes=secaUserPersonalNotes)
        secaUser.save()

        note_content = "This is a note"
        note_problem = Sessions(name="note_1")
        note_problem.save()

        note = Notes(content=note_content)
        note.save()
        note.user.add(secaUser)
        note.session.add(note_problem)
        self.assertEquals(note.content, note_content)
        self.assertEquals(note.user.all()[0], secaUser)
        self.assertEquals(note.session.all()[0], note_problem)

    def test_Notes_multiple_ids(self):
        exampleUser = User(username="name", password="securePassword")
        exampleUser.save()
    
        exampleUser2 = User(username="another_name", password="password2")
        exampleUser2.save()
    
        secaUserPersonalNotes = "this note is different apparently"
        secaUser = SECAUser(user=exampleUser, is_developer=False, notes=secaUserPersonalNotes)
        secaUser.save()
    
        secaUser2 = SECAUser(user=exampleUser2, is_developer=True, notes=secaUserPersonalNotes)
        secaUser2.save()
    
        note_content = "This is a note"
        note_problem = Sessions(name="session_1")
        note_problem.save()
    
        note_2 = Sessions(name="session_2")
        note_2.save()
    
        note = Notes(content=note_content)
        note.save()
        note.user.add(secaUser)
        note.session.add(note_problem)
    
        note2 = Notes(content=note_content)
        note2.save()
        note2.user.add(secaUser2)
        note.session.add(note_2)
    
        self.assertEquals(note.id, 1)
        self.assertEquals(note2.id, 2)
