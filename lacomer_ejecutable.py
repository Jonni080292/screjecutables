import requests
import re
import pandas as pd
from bs4 import BeautifulSoup

import logging
import time



LOG_FILENAME = 'logging_LaComer.out'
logging.basicConfig(filename=LOG_FILENAME,
                    level=logging.DEBUG,
                    )
logging.debug('La Comer')
logging.debug('*************************************')
logging.debug('Inicio : ' + time.strftime("%d/%m/%Y") + '   ' + (time.strftime("%H:%M:%S")))

f = open(LOG_FILENAME, 'rt')
try:
    body = f.read()
finally:
   f.close()

#**************
# cadena conexion sql server
import pyodbc 
server='tcp:orbisprices.database.windows.net'
database='OrbisPrice';
username='PriceExternalLogin@orbisprices'
password='Pr!c3Ext3rn4l082018'

cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)

cursor = cnxn.cursor()
id_item=0


sql_ligas = 'select * from farmacia_ligas where id_farmacia = 5'
tokens = 'select * from tokens '
cursor.execute(sql_ligas)
result = cursor.fetchall()
tokens = 'select rtrim(ltrim(token)) token,rtrim(ltrim(token_asignado)) token_asignado, tipo from tokens'
cursor.execute(tokens)
tokens = cursor.fetchall()

d=[]
for row in tokens:
    d.append({'token':row[0],'asignado':row[1],'tipo':row[2]})          

df = pd.DataFrame(d)

lab='NA'
sustancia='NA'

for row in result:
        print('row = %r' % (row[2],))
        url=row[2]
        start_index = url.find('noPagina')
        cadena2 = len(url)- (start_index+10)
        categoria = row[1]
        #cadena = len(url)-65
       
        url2 =(url[-cadena2:])
        url1 = (url[:start_index])
        
        for numero_pagina in range(row[3]):
            
            url_categoria = url1 + 'noPagina=' + format(numero_pagina+1) + url2
            
            #print(url_categoria)
            #url_categoria = 'https://www.lacomer.com.mx/lacomer/doHome.action?key=Farmacia&succId=14&padreId=6&pasId=1&opcion=listaproductos&path=,6&pathPadre=0&jsp=PasilloPadre.jsp&noPagina=2&mov=1&subOpc=0&agruId=1&succFmt=100&dep=Alimento-para-beb%C3%A9'
            try:
              page = requests.get(url_categoria)
              soup = BeautifulSoup(page.text, 'html.parser')
            except:
               logging.debug('problema conexion ' + url_categoria)
               pass
            #print (soup)


            lista_nombre_productos = soup.find_all(class_='li_producto')
            lista_productos_url = soup.find_all(class_='li_prod_picture')
            #print(len(lista_nombre_productos))
            lista_precio_productos= soup.find_all(class_='li_precios middle-in')
            #print(len(lista_precio_productos))
            lin=0
            producto_nombre_aux = ""
            lab=""
            presentacion=""
            sustancia=""
            precio=0
            precio2=0
            item=0
            promocion=""
            sku=""
            plin= 0
            for producto_name in lista_nombre_productos:
                            try:

                                    prod = producto_name.text

                                    for b in lista_productos_url[item].find_all('a', href=True):
                                       url_imagen = b['href']

                                    for a in producto_name.find_all('a', href=True):
                                       url = a['href'].split('&')
                                       for sku_id in url:
                                           if ( sku_id[:7])=='artEan=':
                                              sku_id = sku_id.replace(" ","")
                                              l = len(sku_id)-7
                                              sku=(sku_id[-l:])
     
                                    lines = (line.strip() for line in prod.splitlines())
                                    # break multi-headlines into a line each
                                    chunks = lines #(phrase.strip() for line in lines for phrase in line.split("  "))
                                    # drop blank lines
                                    text = '\n'.join(chunk for chunk in chunks if chunk)

                                    if len(text.splitlines())<= 4:
                                      for line in text.splitlines():
                                            if lin == 0:
                                              producto_nombre_aux = line
                                            if lin == 1 :
                                              lab = line
                                            if lin == 2 :
                                              presentacion = line + ' '  
                                            if lin == 3 :
                                              presentacion =presentacion + line
                                            lin = lin +1
                                      sustancia = 'NA'
                                    if len(text.splitlines())>= 5:
                                       for line in text.splitlines():
                                            if lin == 0:
                                              producto_nombre_aux = line
                                            if lin == 1 :
                                              lab = line
                                            if lin == 2 :
                                              sustancia = sustancia + line
                                            if lin == 3 :
                                              presentacion = line + ' '  
                                            if lin == 4:
                                              presentacion = presentacion + line
                                            lin = lin +1



                                            
                                    #print(producto)
                                    #print(lab)
                                    #print(presentacion)
                                    #print(sustancia)
                                    #print('precio')
                                   
                                    text = lista_precio_productos[item*2].text
                                    text = text.replace("M.N.","")
                                    text= text.replace(",","")
                                    #print(text)
                                    lines = (line.strip() for line in text.splitlines())
                                    #print(len(text.splitlines()))
                                   
                                    # break multi-headlines into a line each
                                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                                    # drop blank lines
                                    text = '\n'.join(chunk for chunk in lines if chunk)
                                    #print((len(text.splitlines())))
                                    #print(text)

                                    if (len(text.splitlines())) > 1:
                                        for pp in text.splitlines():
                                            pp = pp.replace("M.N.","")
                                            pp= pp.replace(",","")
                                            pp= pp.replace("$","")
                                            if plin == 0:
                                              precio = pp
                                            if plin == 1 and float(pp) > 4: 
                                              precio = pp
                                            plin= plin +1
                                    else:
                                        precio = text

                                    #print(precio)
                                    
                                    producto_nombre_nuevo = producto_nombre_aux.replace("'"," ")
                                    producto_nombre_nuevo= producto_nombre_nuevo.replace("."," ")
                                    producto_nombre_nuevo= producto_nombre_nuevo.replace("(","")                             
                                    presentacion_aux2=presentacion.replace(","," ")
                                    presentacion_aux2=presentacion.replace("."," ")
                                   
                                    item = item +1
                                    id_item = id_item +1

                                    #text mining bag of words
                                    words = producto_nombre_nuevo.split() +  presentacion_aux2.split()
                                    nombre=producto_nombre_nuevo
                                    contenido=" "
                                    unidades=""
                                    unidades2=""
                                    tipo=""
                                    num_unidades=0
                                    num_word=0
                                

                                    for word in words:
                             
                                       a=word.upper()
                                       try:
                                          b=(df.loc[df['token']==a])
                                          if ( b.iloc[0]['tipo']) == 1:
                                             ban=1
                                             contenido = b.iloc[0]['asignado']
                                             nombre = nombre.replace(word,"")
                                             sustancia=sustancia.replace(word,"")
                                             if  (words[num_word -1].isdigit()):
                                                  unidades = words[num_word -1]
                                                  nombre = nombre.replace(words[num_word -1],"")
                                                  sustancia=sustancia.replace(words[num_word -1],"")

                                                 
                                          else:
                                            if tipo=="":
                                              ban=2
                                              tipo=  b.iloc[0]['asignado']
                                              nombre = nombre.replace(word,"")
                                              sustancia=sustancia.replace(word,"")
                                              if  (words[num_word -1].isdigit()):
                                                  unidades2 = words[num_word -1]
                                                  nombre = nombre.replace(words[num_word -1],"")
                                                  sustancia=sustancia.replace(words[num_word -1],"")
                                              
                                       except:
                                         pass
         
                                   
                                       if  re.search(r"[0-9]/[0-9]",a) :
                                       
                                            if num_unidades == 0 and ban==2: 
                                                    unidades2=word
                                                    num_unidades=1
                                            else:
                                                    unidades=word
                                            nombre = nombre.replace(word,"")
                                            sustancia=sustancia.replace(word,"")
                                            unidades2 = word[-1]
                                       else:
                                            
                                            if re.search(r"[0-9][0-9]M*",a) or re.search(r"[0-9][0-9]G*",a) :
                                                a = word[-2:]
                                                a = a.upper()
                                                print(a)
                                                try:
                                                    b=(df.loc[df['token']==a])
                                                    if ( b.iloc[0]['tipo']) == 1:
                                                         contenido = b.iloc[0]['asignado']
                                                         nombre = nombre.replace(word,"")
                                                         sustancia=sustancia.replace(word,"")
                                                    else: 
                                                          tipo=  b.iloc[0]['asignado']
                                                          unidades2 = word[:-2]
                                                          num_unidades=1
                                                          nombre = nombre.replace(word,"")
                                                          sustancia=sustancia.replace(word,"")
                                                except:
                                                    pass
                                                
                                                nombre = nombre.replace(word,"")
                                       num_word = num_word +1 


                      
                                    text = ""
                                    try:
                                      sql = ("insert into Productos values (5," + format(id_item) + ",'" + sku 
                                         + "','" + nombre.strip()
                                         + "','" + producto_nombre_nuevo.strip()
                                         + "','" + lab + "','"
                                         +  sustancia + "','" + presentacion_aux2.strip()
                                         + "','" + contenido.strip()
                                         + "','" + unidades
                                         + "','" + tipo.strip()
                                         + "','" + unidades2 
                                         + "'," + format(precio) + "," + format(categoria)
                                         + ",GETDATE() ,'https://www.lacomer.com.mx/lacomer/" + url_imagen + "')")
                                    #print(sql)
                                      
                                      cursor.execute(sql)
                                      cursor.commit()
                                    except:
                                      logging.debug('error al grabar el registro datos:' +  sql)
                                      pass
                                    lin=0
                                    producto = ""
                                    lab=""
                                    presentacion=""
                                    sustancia=""
                                    precio = 0
                                    plin=0

                            except:
                              
                              logging.debug('Error al leer la página ')
                              pass



try:
    sql = ("exec SP_Actualiza_catalogo 5")
    cursor.execute(sql)
    cursor.commit()
except:
  logging.debug('error al actualizar el catalogo datos:',)
pass

logging.debug('fin La comer: ' + (time.strftime("%H:%M:%S")))
