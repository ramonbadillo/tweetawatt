from xml.dom.minidom import parse, parseString


dom1 = parse('propiedades.xml')
# <membership/>
#document = ElementTree.parse( 'propiedades.xml' )
user = Element( 'user' )
print  user