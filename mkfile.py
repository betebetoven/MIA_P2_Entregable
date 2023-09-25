from FORMATEO.ext2.ext2 import Superblock, Inode, FolderBlock, FileBlock, PointerBlock, block, Content
import os
import struct
import time
import random
from mountingusers import load_users_from_content, parse_users, get_user_if_authenticated, get_id_by_group, extract_active_groups,get_group_id
from FORMATEO.ext2.ext2 import Superblock, Inode, FolderBlock, FileBlock, PointerBlock, block, Content
import struct
from prettytable import PrettyTable
import re

def busca(file,byte,tipo,x):
    if tipo == 0:
        file.seek(byte)
        inodo = Inode.unpack(file.read(Inode.SIZE))
        if inodo.i_type == 1:
            return False, None
        esta = False
        v = None
        for n in inodo.i_block:
            if n == -1:
                continue
            esta,v = busca(file,n,1,x)
            if esta:
                break
        return esta,v
    elif tipo == 1:
        file.seek(byte)
        folder = FolderBlock.unpack(file.read(FolderBlock.SIZE))
        esta = False
        v = None
        for n in folder.b_content:
            #print(f'nombre del nodo {n.b_name} y nombre buscado {x} y numero de inodo {n.b_inodo}')
            if n.b_inodo == -1:
                continue
            if n.b_name.rstrip('\x00') == x:
                #print("si son iguales")
                esta = True
                v = n.b_inodo
                break
        return esta,v
def busca_reseteabloque(file,byte,tipo,x):
    if tipo == 0:
        file.seek(byte)
        inodo = Inode.unpack(file.read(Inode.SIZE))
        if inodo.i_type == 1:
            return False, None
        esta = False
        v = None
        for n in inodo.i_block:
            if n == -1:
                continue
            esta,v = busca_reseteabloque(file,n,1,x)
            if esta:
                break
        return esta,v
    elif tipo == 1:
        file.seek(byte)
        folder = FolderBlock.unpack(file.read(FolderBlock.SIZE))
        esta = False
        v = None
        for i,n in enumerate(folder.b_content):
            #print(f'nombre del nodo {n.b_name} y nombre buscado {x} y numero de inodo {n.b_inodo}')
            if n.b_inodo == -1:
                continue
            if n.b_name.rstrip('\x00') == x:
                #print("si son iguales")
                esta = True
                v = n.b_inodo
                folder.b_content[i].b_name = 'empty'
                folder.b_content[i].b_inodo = -1
                file.seek(byte)
                file.write(folder.pack())
                break
        return esta,v
def busca_renombrabloque(file,byte,tipo,x,y):
    if tipo == 0:
        file.seek(byte)
        inodo = Inode.unpack(file.read(Inode.SIZE))
        if inodo.i_type == 1:
            return False, None
        esta = False
        v = None
        for n in inodo.i_block:
            if n == -1:
                continue
            esta,v = busca_renombrabloque(file,n,1,x,y)
            if esta:
                break
        return esta,v
    elif tipo == 1:
        file.seek(byte)
        folder = FolderBlock.unpack(file.read(FolderBlock.SIZE))
        esta = False
        v = None
        for i,n in enumerate(folder.b_content):
            #print(f'nombre del nodo {n.b_name} y nombre buscado {x} y numero de inodo {n.b_inodo}')
            if n.b_inodo == -1:
                continue
            if n.b_name.rstrip('\x00') == x:
                #print("si son iguales")
                esta = True
                v = n.b_inodo
                folder.b_content[i].b_name = y
                #folder.b_content[i].b_inodo = -1
                file.seek(byte)
                file.write(folder.pack())
                break
        return esta,v
    
def recupera_todos_los_bytes(file,byte,tipo, lista_inodos, lista_bloques):
    #print("entra a recupera con byte ", byte, " y tipo ", tipo)
    if tipo == 0:
        file.seek(byte)
        inodo = Inode.unpack(file.read(Inode.SIZE))
        lista_inodos.append(byte)
        #print(inodo)
        #print(f'inodo {byte}')
        for n in inodo.i_block:
            if n != -1:
                if inodo.i_type == '0':
                    recupera_todos_los_bytes(file,n,1,lista_inodos, lista_bloques)  
                elif inodo.i_type == '1':
                    #print(f'bloque {n}')
                    lista_bloques.append(n)
    elif tipo == 1:
        file.seek(byte)
        folder = FolderBlock.unpack(file.read(FolderBlock.SIZE))
        lista_bloques.append(byte)
        #print(f'bloque {byte}')
        for n in folder.b_content:
            if n.b_inodo != -1:
                recupera_todos_los_bytes(file,n.b_inodo,0,lista_inodos, lista_bloques)
def recorre(file, inicio, tipo, superblock):
    if inicio == -1:
        return -1
    elif tipo == 0:
        file.seek(inicio)
        objeto = Inode.unpack(file.read(Inode.SIZE))
        proceed, newbyte = espacio_libre_bitmap_inodos(file,superblock)
        for i,n in enumerate(objeto.i_block):
            if objeto.i_type == '0':
                x = recorre(file,n,1,superblock)
            elif objeto.i_type == '1':
                x = recorre(file,n,2,superblock)
            objeto.i_block[i] = x
    elif tipo == 1:
        file.seek(inicio)
        objeto = FolderBlock.unpack(file.read(FolderBlock.SIZE))
        proceed, newbyte = espacio_libre_bitmap_bloques(file,superblock)
        for i,n in enumerate(objeto.b_content):
            x = recorre(file,n.b_inodo,0,superblock)
            objeto.b_content[i].b_inodo = x
    elif tipo == 2:
        file.seek(inicio)
        objeto = FileBlock.unpack(file.read(FileBlock.SIZE))
        print("objeto encontrado en "+str(inicio))
        proceed, newbyte = espacio_libre_bitmap_bloques(file,superblock)
    file.seek(newbyte)
    file.write(objeto.pack())
    return newbyte
def espacio_libre_bitmap_bloques(file,superblock):
    bitmap_bloques_inicio = superblock.s_bm_block_start
    cantidad_bloques = superblock.s_blocks_count
    FORMAT = f'{cantidad_bloques}s'
    SIZE = struct.calcsize(FORMAT)
    file.seek(bitmap_bloques_inicio)
    bitmap_bloques = struct.unpack(FORMAT, file.read(SIZE))
    bitmap_bloques=bitmap_bloques[0].decode('utf-8')
    index = bitmap_bloques.find('0')
    if index == -1:
        return False, None
    #write the new slot in the bitmap
    bitmap_bloques=bitmap_bloques[:index] + '1' + bitmap_bloques[index+1:]
    file.seek(bitmap_bloques_inicio)
    
    file.write(bitmap_bloques.encode('utf-8'))
    byte = index_to_byte(index,superblock.s_block_start,block.SIZE)
    return True, byte
def espacio_libre_bitmap_inodos(file,superblock):
    bitmap_inodos_inicio = superblock.s_bm_inode_start
    cantidad_inodos = superblock.s_inodes_count
    FORMAT = f'{cantidad_inodos}s'
    SIZE = struct.calcsize(FORMAT)
    file.seek(bitmap_inodos_inicio)
    bitmap_inodos = struct.unpack(FORMAT, file.read(SIZE))
    bitmap_inodos=bitmap_inodos[0].decode('utf-8')
    index = bitmap_inodos.find('0')
    if index == -1:
        return False, None
    #write the new slot in the bitmap
    bitmap_inodos=bitmap_inodos[:index] + '1' + bitmap_inodos[index+1:]
    file.seek(bitmap_inodos_inicio)
    
    file.write(bitmap_inodos.encode('utf-8'))
    byte = index_to_byte(index,superblock.s_inode_start,Inode.SIZE)
    return True, byte
texto_de_find   = ''
def busca_en_todo_el_sistema(file,byte,tipo,texto,x,contador):
    tabs = '\t'*contador
    global texto_de_find
    if byte == -1:
        return
    if tipo == 0:
        file.seek(byte)
        inodo = Inode.unpack(file.read(Inode.SIZE))
        if inodo.i_type == '1':
            return   
        for n in inodo.i_block:
            if n == -1:
                continue
            busca_en_todo_el_sistema(file,n,1,texto,x,contador)
    if tipo == 1:
        file.seek(byte)
        folder = FolderBlock.unpack(file.read(FolderBlock.SIZE))
        for n in folder.b_content:
            if n.b_inodo == -1:
                continue
            if n.b_name.rstrip('\x00') == x:
                texto += tabs+"|_"+n.b_name.rstrip('\x00') +"  <---------🔎"+"\n"
                texto_de_find = texto
                return
            texto += tabs+"|_"+n.b_name.rstrip('\x00') +"\n"
            nuevo_contador = contador+1
            busca_en_todo_el_sistema(file,n.b_inodo,0,texto,x,nuevo_contador)
def busca_en_todo_el_sistema_regex(file, byte, tipo, texto, x, contador):
    texto = ''
    tabs = '\t' * contador
    regex = None
    if x == '*':
        regex = re.compile(r'^[a-zA-Z0-9_-]+\.txt$')
    elif x == '?':
        regex = re.compile(r'^[a-zA-Z]\.txt$')

    if byte == -1:
        return ''
    if tipo == 0:
        file.seek(byte)
        inodo = Inode.unpack(file.read(Inode.SIZE))
        if inodo.i_type == '1':
            return ''
        for n in inodo.i_block:
            if n == -1:
                continue
            texto += busca_en_todo_el_sistema_regex(file, n, 1, texto, x, contador)
    if tipo == 1:
        file.seek(byte)
        folder = FolderBlock.unpack(file.read(FolderBlock.SIZE))
        for n in folder.b_content:
            if n.b_inodo == -1:
                continue
            # Adjust the comparison based on the value of x
            if regex:
                match = regex.match(n.b_name.rstrip('\x00'))
                if match:
                    texto += tabs + "|_" + n.b_name.rstrip('\x00') + "  <---------🔎" + "\n"
                    continue
    
            texto += tabs + "|_" + n.b_name.rstrip('\x00') + "\n"
            nuevo_contador = contador + 1
            texto += busca_en_todo_el_sistema_regex(file, n.b_inodo, 0, texto, x, nuevo_contador)
    return texto
        

def byte_to_index(byte, inicio, size):
    return (byte - inicio) // size   
def index_to_byte(index, inicio, size):
    return inicio + index*size       
def actualizar_bitmap(file,superblock,lista_inodos,lista_bloques):
    bitmap_bloques_inicio = superblock.s_bm_block_start
    cantidad_bloques = superblock.s_blocks_count
    FORMAT = f'{cantidad_bloques}s'
    SIZE = struct.calcsize(FORMAT)
    file.seek(bitmap_bloques_inicio)
    bitmap_bloques = struct.unpack(FORMAT, file.read(SIZE))
    bitmap_bloques=bitmap_bloques[0].decode('utf-8')
    bitmap_inodos_inicio = superblock.s_bm_inode_start
    cantidad_inodos = superblock.s_inodes_count
    FORMAT = f'{cantidad_inodos}s'
    SIZE = struct.calcsize(FORMAT)
    file.seek(bitmap_inodos_inicio)
    bitmap_inodos = struct.unpack(FORMAT, file.read(SIZE))
    bitmap_inodos=bitmap_inodos[0].decode('utf-8')
    #print("bitmaps antes")
    #print("bloques")
    #print(bitmap_bloques)
    #print("inodos")
    #print(bitmap_inodos)
    for n in lista_inodos:
        index = byte_to_index(n,superblock.s_inode_start,Inode.SIZE)
        bitmap_inodos = bitmap_inodos[:index] + '0' + bitmap_inodos[index+1:]
    for n in lista_bloques:
        index = byte_to_index(n,superblock.s_block_start,block.SIZE)
        bitmap_bloques = bitmap_bloques[:index] + '0' + bitmap_bloques[index+1:]
    file.seek(bitmap_bloques_inicio)
    
    file.write(bitmap_bloques.encode('utf-8'))
    file.seek(bitmap_inodos_inicio)
    
    file.write(bitmap_inodos.encode('utf-8'))
    #print("bitmaps despues")
    #print("bloques")
    #print(bitmap_bloques)
    #print("inodos")
    #print(bitmap_inodos)

        

def busca_espacio_libre(file,byte,tipo):
    x = -1
    if tipo == 0:
        file.seek(byte)
        inodo = Inode.unpack(file.read(Inode.SIZE))
        if inodo.i_type == 1:
            return False, None
        libre = False
        byte_libre = None
        tipo_libre =None
        indice_libre    = None
        for i,n in enumerate(inodo.i_block):
            if n == -1:
                return True,byte,tipo,i
            libre, byte_libre, tipo_libre,indice_libre = busca_espacio_libre(file,n,1)
            if libre:
                break
        return libre, byte_libre, tipo_libre,indice_libre
    elif tipo == 1:
        file.seek(byte)
        folder = FolderBlock.unpack(file.read(FolderBlock.SIZE))
        libre = False
        byte_libre = None
        tipo_libre = 1
        indice_libre    = None
        for i,n in enumerate(folder.b_content):
            #print(f'nombre del nodo {n.b_name} y nombre buscado {x} y numero de inodo {n.b_inodo}')
            if n.b_inodo == -1 and n.b_name.rstrip('\x00') == "empty":
                return True,byte,tipo,i
            
        return False, None, None,None 
def get_file_content(partial_path):
    current_directory = os.getcwd()
    full_path = full_path= f'{current_directory}{partial_path}'
    
    if not os.path.exists(full_path):
        print(f"Error: The file {full_path} does not exist.")
        return ''

    with open(full_path, 'r') as file:
        content = file.read()

    return content   
    
def mkfile(params, mounted_partitions,id, usuario_actual):
    UID = usuario_actual['id']
    GID = UID
    print(f'📜 <<RUNNING MAKE-FILE {params} _ _ _ _ _ _ _ _ _ ')
    if id == None:
        print("Error: The id is required.")
        return
    try: 
        insidepath = params['path']
        r = params.get('r', '/')
        archivosize = params.get('size', 0)
        if archivosize < 0:
            print("Error: tamano negativo")
            return
        archivocont = params.get('cont', '')
        if archivocont != '':
            archivocont = get_file_content(archivocont)
            #print(archivocont)
    except:
        print("Error: The user, password and group are required.")
        return
    partition = None
    for partition_dict in mounted_partitions:
        if id in partition_dict:
            partition = partition_dict[id]
            break
    if not partition:
        print(f"Error: The partition with id {id} does not exist.")
        return
    # Retrieve partition details.
    path = partition['path']
    inicio = partition['inicio']
    size = partition['size']
    filename = path
    current_directory = os.getcwd()
    full_path= f'{current_directory}/discos_test{filename}'
    if not os.path.exists(full_path):
        print(f"Error: The file {full_path} does not exist.")
        return
    with open(full_path, "rb+") as file:
        file.seek(inicio)
        superblock = Superblock.unpack(file.read(Superblock.SIZE))
        lista_direcciones = insidepath.split('/')[1:]
        ##########################################################
        #print(lista_direcciones)
        PI = superblock.s_inode_start
        newI = -1
        for i,n in enumerate(lista_direcciones):
            esta,v = busca(file,PI,0,n)
            if esta:
                PI = v
            else:
                if r != '-r':
                    print(f'archivo {insidepath} no existe')
                    return
                newI = i
                break
        if newI == -1:
            print(f'archivo {insidepath} ya existe')
            return
        ##########################################################
        else:
            
            nueva_lista_dirercciones = lista_direcciones[newI:]
            inodo_inicio = superblock.s_inode_start
            inodo_size = Inode.SIZE
            indice = (PI - inodo_inicio) // inodo_size
            folder_a_escribir = nueva_lista_dirercciones[0]
            #find the first available slot in the current inode
            file.seek(PI)
            inodo_actual = Inode.unpack(file.read(Inode.SIZE))
            indice = -1
            for i,n in enumerate(inodo_actual.i_block):
                if n == -1:
                    indice = i
                    break
            if indice != -1 and i<=12:
                
                bitmap_bloques_inicio = superblock.s_bm_block_start
                cantidad_bloques = superblock.s_blocks_count
                FORMAT = f'{cantidad_bloques}s'
                SIZE = struct.calcsize(FORMAT)
                file.seek(bitmap_bloques_inicio)
                bitmap_bloques = struct.unpack(FORMAT, file.read(SIZE))
                bitmap_bloques=bitmap_bloques[0].decode('utf-8')
                #print(bitmap_bloques)
                bitmap_inodos_inicio = superblock.s_bm_inode_start
                cantidad_inodos = superblock.s_inodes_count
                FORMAT = f'{cantidad_inodos}s'
                SIZE = struct.calcsize(FORMAT)
                file.seek(bitmap_inodos_inicio)
                bitmap_inodos = struct.unpack(FORMAT, file.read(SIZE))
                bitmap_inodos=bitmap_inodos[0].decode('utf-8')
                #print(bitmap_inodos)
                
                
                a,b,c,d = busca_espacio_libre(file,PI,0)
                if c == 0:
                    #print(f'{a}byte libre {b} tipo libre inodo indice libre {d}')
                    index_bloque_inicial = bitmap_bloques.find('0')
                    bitmap_bloques=bitmap_bloques[:index_bloque_inicial] + '1' + bitmap_bloques[index_bloque_inicial+1:]
                    byte_nuevo_bloque = superblock.s_block_start + index_bloque_inicial*block.SIZE
                    file.seek(b)
                    inodo_presente = Inode.unpack(file.read(Inode.SIZE))
                    inodo_presente.i_block[d] = byte_nuevo_bloque
                    file.seek(b)
                    file.write(inodo_presente.pack())
                    nuevo_bloque = FolderBlock()
                    #actualiza el inodo actual con la direccion del nuevo bloque necesario para ambos casos y lo escribe en el disco
                    ####################################
                    
                    index_nodo = bitmap_inodos.find('0')
                    bitmap_inodos=bitmap_inodos[:index_nodo] + '1' + bitmap_inodos[index_nodo+1:]
                    byte_nuevo_inodo2 = superblock.s_inode_start + index_nodo*Inode.SIZE
                    
                    ####################################
                    nuevo_bloque.b_content[0].b_name = folder_a_escribir
                    nuevo_bloque.b_content[0].b_inodo = byte_nuevo_inodo2
                    file.seek(byte_nuevo_bloque)
                    file.write(nuevo_bloque.pack())
                    #_________________________________________________________________
                    nuevo_inodo = Inode()
                    nuevo_inodo.i_uid = int(UID)
                    nuevo_inodo.I_gid = int(GID)    
                    nuevo_inodo.i_s = int(archivosize)
                    nuevo_inodo.i_perm = 664
                    if not folder_a_escribir.endswith('.txt'):
                        index_bloque = bitmap_bloques.find('0')
                        bitmap_bloques=bitmap_bloques[:index_bloque] + '1' + bitmap_bloques[index_bloque+1:]
                        byte_nuevo_bloque2 = superblock.s_block_start + index_bloque*block.SIZE
                        nuevo_inodo.i_block[0] = byte_nuevo_bloque2
                        file.seek(byte_nuevo_inodo2)
                        file.write(nuevo_inodo.pack())
                        nuevo_bloque = FolderBlock()
                        file.seek(byte_nuevo_bloque2)
                        file.write(nuevo_bloque.pack())
                        #escribe de nuevo los bitmaps
                        file.seek(bitmap_bloques_inicio)
                        
                        file.write(bitmap_bloques.encode('utf-8'))
                        file.seek(bitmap_inodos_inicio)
                        
                        file.write(bitmap_inodos.encode('utf-8'))
                        dict = {'path':'/home'}
                        #mkfile(params,mounted_partitions,id, usuario_actual)
                    else:
                        #REVISA LOS BITMAPS AQUI, NO TE CONFIES
                        nuevo_inodo.i_type = '1'
                        file.seek(byte_nuevo_inodo2)
                        file.write(nuevo_inodo.pack())
                        #nuevo_bloque = FileBlock()
                        #file.seek(byte_nuevo_bloque)
                        #file.write(nuevo_bloque.pack())
                        #escribe de nuevo los bitmaps
                        file.seek(bitmap_bloques_inicio)
                        
                        file.write(bitmap_bloques.encode('utf-8'))
                        file.seek(bitmap_inodos_inicio)
                        
                        file.write(bitmap_inodos.encode('utf-8'))
                        dict = {'path':'/home'}
                        #NOW WRITE THE CONTENT OF THE FILE IF ARCHIVOCONT IS NOT EMPTY
                        if archivocont!='':
                            
                            length = len(archivocont)
                            fileblocks = length//64
                            if length%64 != 0:
                                fileblocks += 1
                            indice_bloque = bitmap_bloques.find('0'*fileblocks)
                            bitmap_bloques = bitmap_bloques[:indice_bloque] + '1'*fileblocks + bitmap_bloques[indice_bloque+fileblocks:]
                            if fileblocks<=12:
                                texto = archivocont 
                                chunks = [texto[i:i+64] for i in range(0, len(texto), 64)]
                                primerbloque = superblock.s_block_start + indice_bloque*block.SIZE
                                for i,n in enumerate(chunks):
                                    new_fileblock = FileBlock()
                                    new_fileblock.b_content = n
                                    nuevo_inodo.i_block[i] = primerbloque+i*64
                                    file.seek(primerbloque+i*64)
                                    file.write(new_fileblock.pack())
                                nuevo_inodo.i_s = fileblocks*64
                                file.seek(byte_nuevo_inodo2)
                                file.write(nuevo_inodo.pack())
                                file.seek(bitmap_bloques_inicio)
                                
                                file.write(bitmap_bloques.encode('utf-8'))
                        
                        
                        
                        
                        
                        
                        return
                    
                    
                    
                    
                    
                    
                    
                    
                elif c == 1:
                    #solo se necesita un inodo y un folderblock nuevos
                    #crea en los inodos el nuevo inodo y el nuevo bloque
                    
                    index_nodo = bitmap_inodos.find('0')
                    
                    bitmap_inodos=bitmap_inodos[:index_nodo] + '1' + bitmap_inodos[index_nodo+1:]
                    byte_nuevo_inodo = superblock.s_inode_start + index_nodo*Inode.SIZE
        
                    #obtiene el index del nuevo inodo y el nuevo bloque
                    file.seek(b)
                    bloque_actual = FolderBlock.unpack(file.read(FileBlock.SIZE))
                    bloque_actual.b_content[d].b_name = folder_a_escribir
                    bloque_actual.b_content[d].b_inodo = byte_nuevo_inodo
                    file.seek(b)
                    file.write(bloque_actual.pack())
                    #actualiza el bloque actual con la direccion del nuev oinodo
                    nuevo_inodo = Inode()
                    nuevo_inodo.i_uid = int(UID)
                    nuevo_inodo.I_gid = int(GID)
                    nuevo_inodo.i_s = int(archivosize)
                    nuevo_inodo.i_perm = 664
                    #inicializa nuevo inodo pero aun no ingresa el bloque
                    if not folder_a_escribir.endswith('.txt'):
                        index_bloque = bitmap_bloques.find('0')
                        bitmap_bloques=bitmap_bloques[:index_bloque] + '1' + bitmap_bloques[index_bloque+1:]
                        byte_nuevo_bloque = superblock.s_block_start + index_bloque*block.SIZE
                        nuevo_inodo.i_block[0] = byte_nuevo_bloque
                        file.seek(byte_nuevo_inodo)
                        file.write(nuevo_inodo.pack())
                        #agrega direccion del bloque creado arriba al principio al inodo
                        nuevo_bloque = FolderBlock()
                        file.seek(byte_nuevo_bloque)
                        file.write(nuevo_bloque.pack())
                        #escribe el nuevo bloque en el disco
                        #escribe de nuevo los bitmaps
                        file.seek(bitmap_bloques_inicio)
                        
                        file.write(bitmap_bloques.encode('utf-8'))
                        file.seek(bitmap_inodos_inicio)
                        
                        file.write(bitmap_inodos.encode('utf-8'))
                        dict = {'path':'/home'}
                        #mkfile(params,mounted_partitions,id, usuario_actual)
                    else:
                        #REVISA LOS BITMAPS AQUI, NO TE CONFIES
                        nuevo_inodo.i_type = '1'
                        file.seek(byte_nuevo_inodo)
                        file.write(nuevo_inodo.pack())
                        #nuevo_bloque = FileBlock()
                        #file.seek(byte_nuevo_bloque)
                        #file.write(nuevo_bloque.pack())
                        #escribe de nuevo los bitmaps
                        #file.seek(bitmap_bloques_inicio)
                        #file.write(bitmap_bloques.encode('utf-8'))
                        file.seek(bitmap_inodos_inicio)
                        
                        file.write(bitmap_inodos.encode('utf-8'))
                        dict = {'path':'/home'}
                        #NOW WRITE THE CONTENT OF THE FILE IF ARCHIVOCONT IS NOT EMPTY
                        if archivocont!='':
                            
                            length = len(archivocont)
                            fileblocks = length//64
                            if length%64 != 0:
                                fileblocks += 1
                            indice_bloque = bitmap_bloques.find('0'*fileblocks)
                            bitmap_bloques = bitmap_bloques[:indice_bloque] + '1'*fileblocks + bitmap_bloques[indice_bloque+fileblocks:]
                            if fileblocks<=12:
                                texto = archivocont 
                                chunks = [texto[i:i+64] for i in range(0, len(texto), 64)]
                                primerbloque = superblock.s_block_start + indice_bloque*block.SIZE
                                for i,n in enumerate(chunks):
                                    new_fileblock = FileBlock()
                                    new_fileblock.b_content = n
                                    nuevo_inodo.i_block[i] = primerbloque+i*64
                                    file.seek(primerbloque+i*64)
                                    file.write(new_fileblock.pack())
                                nuevo_inodo.i_s = fileblocks*64
                                file.seek(byte_nuevo_inodo)
                                file.write(nuevo_inodo.pack())
                                file.seek(bitmap_bloques_inicio)
                                
                                file.write(bitmap_bloques.encode('utf-8'))
                        
                        
                        
                        
                        
                        return
                    #mkfile(dict,mounted_partitions,id)
    if newI != -1:    
        
        mkfile(params,mounted_partitions,id, usuario_actual)
                    
                    
                #implementar agragar folder o file(da lo mismo reutiliza codigo) si nos encontramos en un slot libre de un inodo
                #resolver pq no funciona la recursividad para compmlentar toda la direccion necesarai ingresada
                
                
def cat(params, mounted_partitions,id, usuario_actual):  
    print(f'🐈 <<RUNNING CAT {params} _ _ _ _ _ _ _ _ _ ')
    if id == None:
        print("Error: The id is required.")
        return
    insidepaths = []  
    insidepath1 = params.get('file1', '')
    if insidepath1 != '':
        insidepaths.append(insidepath1)
    insidepath2 = params.get('file2', '')
    if insidepath2 != '':
        insidepaths.append(insidepath2)
    insidepath3 = params.get('file3', '')
    if insidepath3 != '':
        insidepaths.append(insidepath3)
    insidepath4 = params.get('file4', '')
    if insidepath4 != '':
        insidepaths.append(insidepath4)
    for n in insidepaths:
        print(n)
    partition = None
    for partition_dict in mounted_partitions:
        if id in partition_dict:
            partition = partition_dict[id]
            break
    if not partition:
        print(f"Error: The partition with id {id} does not exist.")
        return
    # Retrieve partition details.
    path = partition['path']
    inicio = partition['inicio']
    size = partition['size']
    filename = path
    current_directory = os.getcwd()
    full_path= f'{current_directory}/discos_test{filename}'
    if not os.path.exists(full_path):
        print(f"Error: The file {full_path} does not exist.")
        return
    with open(full_path, "rb+") as file:
        file.seek(inicio)
        superblock = Superblock.unpack(file.read(Superblock.SIZE))
        for insidepath in insidepaths:
            print(f'\n\nCAT DE {insidepath} ')
            lista_direcciones = insidepath.split('/')[1:]
            ##########################################################
            PI = superblock.s_inode_start
            newI = -1
            for i,n in enumerate(lista_direcciones):
                esta,v = busca(file,PI,0,n)
                if esta:
                    PI = v
                else:
                    print(f'archivo {insidepath} no existe')
                    newI = i
                    return
            if newI == -1:
                print("#############################################")
                print(f'archivo {insidepath} ya existe')
                print(f'byte del inodo {PI}')
                file.seek(PI)
                inodo = Inode.unpack(file.read(Inode.SIZE))
                print(inodo)
                #print(inodo.i_block)
                print("#############################################")
                texto = ''
                for n in inodo.i_block:
                    if n == -1:
                        continue
                    file.seek(n)
                    bloque = FileBlock.unpack(file.read(FileBlock.SIZE))
                    texto +=bloque.b_content.strip('\x00')
                print(texto)
                print("#############################################")
                
                
            ##########################################################
    
def remove(params, mounted_partitions,id, usuario_actual):  
    print(f'💀 <<RUNNING REMOVE {params} _ _ _ _ _ _ _ _ _ ')
    if id == None:
        print("Error: The id is required.")
        return
    try: 
        insidepath = params['path']
    except:
        print("Error:Path must be specified.")
        return
    partition = None
    for partition_dict in mounted_partitions:
        if id in partition_dict:
            partition = partition_dict[id]
            break
    if not partition:
        print(f"Error: The partition with id {id} does not exist.")
        return
    # Retrieve partition details.
    path = partition['path']
    inicio = partition['inicio']
    size = partition['size']
    filename = path
    current_directory = os.getcwd()
    full_path= f'{current_directory}/discos_test{filename}'
    if not os.path.exists(full_path):
        print(f"Error: The file {full_path} does not exist.")
        return
    with open(full_path, "rb+") as file:
        file.seek(inicio)
        superblock = Superblock.unpack(file.read(Superblock.SIZE))
        
        lista_direcciones = insidepath.split('/')[1:]
        PI = superblock.s_inode_start
        for i,n in enumerate(lista_direcciones):
            if i == len(lista_direcciones)-1:
                esta,v = busca_reseteabloque(file,PI,0,n)
            else:
                esta,v = busca(file,PI,0,n)
            if esta:
                PI = v
            else:
                print(f'archivo {insidepath} no existe')
                return
        inodos = []
        bloques = []
        recupera_todos_los_bytes(file,PI,0,inodos,bloques)
        #print(inodos)
        #print(bloques)
        index_inodos = []
        for n in inodos:
            index_inodos.append(byte_to_index(n,superblock.s_inode_start,Inode.SIZE))
        index_bloques = []
        for n in bloques:
            index_bloques.append(byte_to_index(n,superblock.s_block_start,block.SIZE))
        #print(index_inodos)
        #print(index_bloques)
        actualizar_bitmap(file,superblock,inodos,bloques)
        #view bitmaps from file
        file.seek(superblock.s_bm_block_start)
        bitmap_bloques = struct.unpack(f'{superblock.s_blocks_count}s', file.read(superblock.s_blocks_count))[0].decode('utf-8')
        file.seek(superblock.s_bm_inode_start)
        bitmap_inodos = struct.unpack(f'{superblock.s_inodes_count}s', file.read(superblock.s_inodes_count))[0].decode('utf-8')
        #print("inodos")
        #print(bitmap_inodos)
        #print("bloques")
        #print(bitmap_bloques)
        #print("")
        print(f'archivo {insidepath} eliminado')
        
    
        
def rename(params, mounted_partitions,id, usuario_actual):  
    print(f'🏳️ <<RUNNING RENAME {params} _ _ _ _ _ _ _ _ _ ')
    if id == None:
        print("Error: The id is required.")
        return
    try: 
        insidepath = params['path']
        name = params['name']
    except:
        print("Error:Path must be specified.")
        return
    partition = None
    for partition_dict in mounted_partitions:
        if id in partition_dict:
            partition = partition_dict[id]
            break
    if not partition:
        print(f"Error: The partition with id {id} does not exist.")
        return
    # Retrieve partition details.
    path = partition['path']
    inicio = partition['inicio']
    size = partition['size']
    filename = path
    current_directory = os.getcwd()
    full_path= f'{current_directory}/discos_test{filename}'
    if not os.path.exists(full_path):
        print(f"Error: The file {full_path} does not exist.")
        return
    with open(full_path, "rb+") as file:
        file.seek(inicio)
        superblock = Superblock.unpack(file.read(Superblock.SIZE))
        
        lista_direcciones = insidepath.split('/')[1:]
        PI = superblock.s_inode_start
        for i,n in enumerate(lista_direcciones):
            if i == len(lista_direcciones)-1:
                esta,v = busca_renombrabloque(file,PI,0,n,name)
            else:
                esta,v = busca(file,PI,0,n)
            if esta:
                PI = v
            else:
                print(f'archivo {insidepath} no existe')
                return
def copy(params, mounted_partitions,id, usuario_actual):  
    print(f'🏳️ <<RUNNING COPY {params} _ _ _ _ _ _ _ _ _ ')
    if id == None:
        print("Error: The id is required.")
        return
    try: 
        insidepath = params['path']
        destinypath = params['destino']
    except:
        print("Error:Path must be specified.")
        return
    partition = None
    for partition_dict in mounted_partitions:
        if id in partition_dict:
            partition = partition_dict[id]
            break
    if not partition:
        print(f"Error: The partition with id {id} does not exist.")
        return
    # Retrieve partition details.
    path = partition['path']
    inicio = partition['inicio']
    size = partition['size']
    filename = path
    current_directory = os.getcwd()
    full_path= f'{current_directory}/discos_test{filename}'
    if not os.path.exists(full_path):
        print(f"Error: The file {full_path} does not exist.")
        return
    with open(full_path, "rb+") as file:
        file.seek(inicio)
        superblock = Superblock.unpack(file.read(Superblock.SIZE))
        
        lista_direcciones = insidepath.split('/')[1:]
        PI = superblock.s_inode_start
        for i,n in enumerate(lista_direcciones):
            esta,v = busca(file,PI,0,n)
            if esta:
                PI = v
            else:
                print(f'archivo {insidepath} no existe')
                return
        #print(PI)
        
        lista_direcciones_destino = destinypath.split('/')[1:]
        PI_destino = superblock.s_inode_start
        for i,n in enumerate(lista_direcciones_destino):
            esta,v = busca(file,PI_destino,0,n)
            if esta:
                PI_destino = v
            else:
                print(f'archivo {destinypath} no existe')
                return
        #print(PI_destino)
        a,b,c,d = busca_espacio_libre(file,PI_destino,0)
        inodo_copia_byte = recorre(file,PI,0, superblock)
        if c == 0:
            file.seek(b)
            inodo = Inode.unpack(file.read(Inode.SIZE))
            proceed, byte_bloque = espacio_libre_bitmap_bloques(file,superblock)
            inodo.i_block[d] = byte_bloque
            file.seek(b)
            file.write(inodo.pack())
            new_added_folderblock = FolderBlock()
            new_added_folderblock.b_content[0].b_name = lista_direcciones[-1]
            new_added_folderblock.b_content[0].b_inodo = inodo_copia_byte
            file.seek(byte_bloque)
            file.write(new_added_folderblock.pack())
            print(f'archivo {insidepath} copiado a {destinypath}')
        if c==1:
            file.seek(b)
            #print("ESTE ES EL PI DESTINO")
            #print(b)
            folder = FolderBlock.unpack(file.read(FolderBlock.SIZE))
            folder.b_content[d].b_name = lista_direcciones[-1]
            folder.b_content[d].b_inodo = inodo_copia_byte
            file.seek(b)
            file.write(folder.pack())
            print(f'archivo {insidepath} copiado a {destinypath}')
            
def move(params, mounted_partitions,id, usuario_actual):  
    print(f'🚀 <<RUNNING MOVE {params} _ _ _ _ _ _ _ _ _ ')
    if id == None:
        print("Error: The id is required.")
        return
    try: 
        insidepath = params['path']
        destinypath = params['destino']
    except:
        print("Error:Path must be specified.")
        return
    partition = None
    for partition_dict in mounted_partitions:
        if id in partition_dict:
            partition = partition_dict[id]
            break
    if not partition:
        print(f"Error: The partition with id {id} does not exist.")
        return
    # Retrieve partition details.
    path = partition['path']
    inicio = partition['inicio']
    size = partition['size']
    filename = path
    current_directory = os.getcwd()
    full_path= f'{current_directory}/discos_test{filename}'
    if not os.path.exists(full_path):
        print(f"Error: The file {full_path} does not exist.")
        return
    with open(full_path, "rb+") as file:
        file.seek(inicio)
        superblock = Superblock.unpack(file.read(Superblock.SIZE))
        
        lista_direcciones = insidepath.split('/')[1:]
        PI = superblock.s_inode_start
        for i,n in enumerate(lista_direcciones):
            if i == len(lista_direcciones)-1:
                esta,v = busca_reseteabloque(file,PI,0,n)
            else:
                esta,v = busca(file,PI,0,n)
            if esta:
                PI = v
            else:
                print(f'archivo {insidepath} no existe')
                return
        #print(PI)
        
        lista_direcciones_destino = destinypath.split('/')[1:]
        PI_destino = superblock.s_inode_start
        for i,n in enumerate(lista_direcciones_destino):
            esta,v = busca(file,PI_destino,0,n)
            if esta:
                PI_destino = v
            else:
                print(f'archivo {destinypath} no existe')
                return
        #print(PI_destino)
        a,b,c,d = busca_espacio_libre(file,PI_destino,0)
        inodo_copia_byte = PI
        if c == 0:
            file.seek(b)
            inodo = Inode.unpack(file.read(Inode.SIZE))
            proceed, byte_bloque = espacio_libre_bitmap_bloques(file,superblock)
            inodo.i_block[d] = byte_bloque
            file.seek(b)
            file.write(inodo.pack())
            new_added_folderblock = FolderBlock()
            new_added_folderblock.b_content[0].b_name = lista_direcciones[-1]
            new_added_folderblock.b_content[0].b_inodo = inodo_copia_byte
            file.seek(byte_bloque)
            file.write(new_added_folderblock.pack())
            print(f'archivo {insidepath} movido a {destinypath}')
        if c==1:
            file.seek(b)
            #print("ESTE ES EL PI DESTINO")
            #print(b)
            folder = FolderBlock.unpack(file.read(FolderBlock.SIZE))
            folder.b_content[d].b_name = lista_direcciones[-1]
            folder.b_content[d].b_inodo = inodo_copia_byte
            file.seek(b)
            file.write(folder.pack())
            print(f'archivo {insidepath} movido a {destinypath}')
def find(params, mounted_partitions,id, usuario_actual):  
    print(f'🔍 <<RUNNING FIND {params} _ _ _ _ _ _ _ _ _ ')
    print(f'\n\n🔻____________________________________\n')
    if id == None:
        print("Error: The id is required.")
        return
    try: 
        insidepath = params['path']
        name = params['name']
    except:
        print("Error:Path must be specified.")
        return
    partition = None
    for partition_dict in mounted_partitions:
        if id in partition_dict:
            partition = partition_dict[id]
            break
    if not partition:
        print(f"Error: The partition with id {id} does not exist.")
        return
    # Retrieve partition details.
    path = partition['path']
    inicio = partition['inicio']
    size = partition['size']
    filename = path
    current_directory = os.getcwd()
    full_path= f'{current_directory}/discos_test{filename}'
    if not os.path.exists(full_path):
        print(f"⚠️ Error: The file {full_path} does not exist.")
        return
    with open(full_path, "rb+") as file:
        file.seek(inicio)
        superblock = Superblock.unpack(file.read(Superblock.SIZE))
        
        lista_direcciones = insidepath.split('/')[1:]
        PI = superblock.s_inode_start
        
        for i,n in enumerate(lista_direcciones):
            esta,v = busca(file,PI,0,n)
            if esta:
                PI = v
            else:
                print(f'⚠️ archivo {insidepath} no existe')
                return
        #print(PI)
        global texto_de_find
        texto_de_find = ''
        if name != '*' and name != '?':
            #print(f'entrando a find normal')
            busca_en_todo_el_sistema(file,PI,0,'',name,0)
        else:
            texto_de_find = busca_en_todo_el_sistema_regex(file,PI,0,'',name,0)
        table = PrettyTable()
        table.field_names = [f'--------carpeta de inicio {insidepath} y nombre {name}----------']
        table.align = "l"
        if texto_de_find == '':
            table.add_row([f'⚠️ no se encontro el archivo {name} en la carpeta {insidepath}'])
        else:
            table.add_row(['🏚️'])
            table.add_row([texto_de_find])

        print(table)
        print("🔺- - - - - - - - - - - - - - - - -")