from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
import base64
from pathlib import Path
from .models import Problem_wiki, Content_wiki
from SECAAlgo.models import Sessions
import os
import ast
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.http import HttpResponse

@method_decorator(csrf_exempt, name='dispatch')
class WikiView(View):
    
    def put(self, request):
        """
        The PUT endpoint is responsible for updating Problem wiki title and introduction. This endpoint
        corresponds to the updateTitleIntro/ path defined in urls.py.

        :param request: The HTTP Request object, which has a JSON object in its body. The JSON object has three 
            key value pairs. The first key is the session_id. The other two are the title and intro, 
            both of which are used to update the Problem_Wiki entry corresponding to the given session_id. 
        :return HttpResponse: A HttpResponse is returned on success, if the given session_id is invalid, the a
            404 error is returned instead. 
        """
        byte_str = request.body
        dict_str = byte_str.decode("UTF-8")
        data = dict(ast.literal_eval(dict_str))
        problem_id = data['session_id']
        session = get_object_or_404(Sessions, id=problem_id)
        problem = Problem_wiki.objects.filter(session=session)
        if len(problem) > 0:
            problem = problem[0]
        else:
            return JsonResponse({"issue": 404})
        problem.title = data['title']
        problem.intro = data['intro']
        problem.save()
        return HttpResponse("success")
    
    def delete(self, request):
        """
        The DELETE endpoint is responsible for deleting a Content_Wiki istance. This endpoint
        corresponds to the remove_wiki/ path defined in urls.py.

        :param request: The HTTP Request object, which has two query parameters. Namely, session_id and class. 
        :return HttpResponse: A HttpResponse is returned on success, if the given session_id is invalid, the a
            404 error is returned instead. 
        """
        data = request.GET
        session_id = data.get('session_id')
        className = data.get('class')

        session = get_object_or_404(Sessions, id=session_id)
        problem = Problem_wiki.objects.filter(session=session)
        if len(problem) > 0:
            problem = problem[0]
        else:
            return JsonResponse({"issue": 404})
        toDelete = Content_wiki.objects.filter(name = className, problem_wiki = problem)
        toDelete.delete()
        return HttpResponse("deleted", status=200)
    
    def post(self, request, *args, **kwargs):
        """
        The POST endpoint is responsible for adding a new Content_Wiki istance. This endpoint
        corresponds to the add_wiki/ path defined in urls.py.

        :param request: The HTTP Request object, which has JSON object in body. This JSON object has five key value pairs.
            The keys are: file, session_id, className, description, concepts. 
            session_id is used to query the relevant Problem_Wiki instace, whereas the other values are used
            to populate a new Content_Wiki instance.
        :return HttpResponse: A HttpResponse is returned on success, if the given session_id is invalid, the a
            404 error is returned instead. 
        """
        byte_str = request.body
        dict_str = byte_str.decode("UTF-8")
        data = dict(ast.literal_eval(dict_str))
        img = data['file']
        imageFolder = Path(__file__).resolve().parent
        session_id = int(data['session_id'])
        session = get_object_or_404(Sessions, id=session_id)
        problem = Problem_wiki.objects.filter(session=session)
        if len(problem) > 0:
            problem = problem[0]
        else:
            return JsonResponse({"issue": 404})
        a = Content_wiki(problem_wiki=problem, name=data['className'], description=data['description'],
                         concepts=data['concepts'], image=data['className'] + ".png")
        a.save()
        if(img!="no change"):
            with open(os.path.join(imageFolder, data['className'] + ".png"), "wb") as fh:
                fh.write(base64.decodebytes(bytes(img, 'utf-8')))
        return HttpResponse("success")
    
    def get(self, request):
        """
        The GET endpoint is responsible for adding a new Content_Wiki istance. This endpoint
        corresponds to the expertBackground/ path defined in urls.py.

        :param request: The HTTP Request object, which has one query parameter, session_id. 
            The given session_id is used to retrieve all Problem_Wiki instances that have that foreign key. 
            Then the images of the Problem_Wiki instances are retured along with other data. 
            
        :return HttpResponse: A HttpResponse is returned on success, if the given session_id is invalid, the a
            404 error is returned instead. 
        """
        session_id = int(request.GET.get("session_id", 1))
        session = get_object_or_404(Sessions, id=session_id)
        problem = Problem_wiki.objects.filter(session=session)
        if len(problem) > 0:
            problem = problem[0]
        else:
            return JsonResponse({"issue": 404})
        contents = Content_wiki.objects.filter(problem_wiki=problem)

        images = []
        contents_list = []
        for i in contents:
            img = ""
            with open(os.path.join(Path(__file__).resolve().parent, i.image), "rb") as image:
                img = image.read()
                img = base64.b64encode(img).decode('utf-8')
                images.append(img)
            contents_list.append({
                'class': i.name,
                'description': i.description,
                'expert concepts': i.concepts,
                'image': img
            })

        data = {
            'title': problem.title,
            'intro': problem.intro,
            'image': problem.image,
            'titles': ['Class', 'General Description', 'Expected concepts', 'Example Image'],
            'contents': contents_list
        }
        return JsonResponse(data)
