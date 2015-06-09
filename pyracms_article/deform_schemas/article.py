'''
Deform Schemas for article module.
'''
from colander import MappingSchema, SchemaNode, String
from deform.widget import TextAreaWidget, TextInputWidget
    
class EditArticleSchema(MappingSchema):
    display_name = SchemaNode(String(), widget=TextInputWidget(size=40),
                              missing='')
    article = SchemaNode(String(), widget=TextAreaWidget(cols=140, rows=20))
    summary = SchemaNode(String(), widget=TextInputWidget(size=40), missing='')
    tags = SchemaNode(String(), widget=TextInputWidget(size=40),
                      missing='')