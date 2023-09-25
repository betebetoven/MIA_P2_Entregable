from FORMATEO.ext2.ext2 import Superblock, Inode, FolderBlock, FileBlock, PointerBlock, block, Content, Journal
import os
import struct
import time
import random
from mountingusers import load_users_from_content, parse_users, get_user_if_authenticated, get_id_by_group, extract_active_groups,get_group_id
def mkfs(params, mounted_partitions, users):
    print(f'⚙️<<RUNNING MKFS {params}_ _ _ _ _ _ _ _ _ ')
    tipo = params.get('type', 'full').lower()
    id = params.get('id', None)
    fsext = params.get('fs', 'ext2')
    ext = 2
    if fsext == 'ext3':
        ext = 3
    
    # Check if the id exists in mounted_partitions.
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
    

    # Step 3: Format based on tipo.
    if tipo == 'full':
        print(f'size de particion: {size}')
        superblock = Superblock(inicio, int(size),ext)
        superblock.ver_bytes_inidices()
        superblock.s_free_inodes_count -= 1
        superblock.s_free_blocks_count -= 1 #for the superblock
        filename = path
        current_directory = os.getcwd()
        full_path= f'{current_directory}/discos_test{filename}'
        if not os.path.exists(full_path):
            print(f"Error: The file {full_path} does not exist.")
            return
        with open(full_path, "rb+") as file:
            
            bitmapinodos = ['0']*superblock.s_inodes_count
            bitmapbloques = ['0']*superblock.s_blocks_count
            #fill partition from inicio to size with null bytes
            file.seek(inicio)
            file.write(b'\x00'*size)        
            
            
            #crea inodo 0
            i1 = Inode()
            i1.i_type = '0'
            i1.i_block[0] = superblock.s_block_start
            #crea bloque 0
            b1 = FolderBlock()
            b1.b_content[0].b_inodo = superblock.s_inode_start+Inode.SIZE
            b1.b_content[0].b_name = 'users.txt'
            bitmapbloques[0] = '1'
            bitmapinodos[0] = '1'
            
            
            #crea inodo 1
            i2 = Inode()
            i2.i_type = '1'
            i2.i_block[0] = superblock.s_block_start+block.SIZE
            #crea bloque 1
            b2 = FileBlock()
            b2.b_content = '1,G,root\n1,U,root,root,123\n'
            #b2.b_content+='2,G,usuarios\n2,U,usuarios,user1,usuario\n'
            #users.update(load_users_from_content(b2.b_content))
            #b2.b_content='albertojosuuehernandezarmasdelalibertadalasnacionesdecritsojesusenlasalturasamen'
            bitmapbloques[1] = '1'
            bitmapinodos[1] = '1'
            
            
            
            file.seek(inicio)
            file.write(superblock.pack())
            if ext == 3:
                jrnl = Journal()
                jrnl.journal_data = str(('mkfs',params))+"\n"
                file.write(jrnl.pack())
            
            for i in range(superblock.s_inodes_count):
                file.write(bitmapinodos[i].encode('utf-8'))
            for i in range(superblock.s_blocks_count):
                file.write(bitmapbloques[i].encode('utf-8'))
            file.seek(superblock.s_inode_start)
            file.write(i1.pack())
            file.write(i2.pack())
            file.seek(superblock.s_block_start)
            file.write(b1.pack())
            file.write(b2.pack())
            print(f"Partition {id} was formatted successfully.")
            #print("     bitmap inodos")
            #print(f'    {bitmapinodos}')
            #print("     bitmap bloques")
            #print(f'    {bitmapbloques}')
            

        


        #print(f"Partition {id} was formatted successfully.")
from FORMATEO.ext2.ext2 import Superblock, Inode, FolderBlock, FileBlock, PointerBlock, block, Content
import struct
def login(params, mounted_partitions):
    print(f'🧍<<RUNNING LOGIN {params}_ _ _ _ _ _ _ _ _ ')
#user, password need to come in params, if not, return error
    try:
        user = params['user']
        password = params['pass']
        id = params['id']
        
    except:
        print("Error: The user and password are required.")
        return None, None
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
        #print("ESTE ES EL SUPERBLOCK EN EL LOGIN__________________")
        #print(superblock)
        file.seek(superblock.s_inode_start)
        inodo = Inode.unpack(file.read(Inode.SIZE))
        siguiente = inodo.i_block[0]
        file.seek(siguiente)
        folder = FolderBlock.unpack(file.read(FolderBlock.SIZE))
        siguiente = folder.b_content[0].b_inodo
        file.seek(siguiente)
        inodo = Inode.unpack(file.read(Inode.SIZE))
        texto = ""
        for n in inodo.i_block:
            if n != -1:
                siguiente = n
                file.seek(siguiente)
                fileblock = FileBlock.unpack(file.read(FileBlock.SIZE))
                texto += fileblock.b_content.rstrip('\x00')
        #print("ESTE ES EL TEXTO EN EL LOGIN__________________")
        
        #texto+='2,G,usuarios\n2,U,usuarios,user1,usuario\n'
        #usuarios = load_users_from_content(texto)
        usuarios = parse_users(texto)
        users= get_user_if_authenticated(usuarios, user, password)
        print("ESTE ES EL USUARIO EN EL LOGIN__________________")
        print(users)
        return users,id
        
def makeuser(params, mounted_partitions,id):
    print(f'🙋 <<RUNNING MAKE-USER {params} _ _ _ _ _ _ _ _ _ ')
    #print(params)
    if id == None:
        print("Error: The id is required.")
        return
    try: 
        user = params['user']
        password = params['pass']
        group = params['grp']
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
        file.seek(superblock.s_inode_start)
        inodo = Inode.unpack(file.read(Inode.SIZE))
        siguiente = inodo.i_block[0]
        file.seek(siguiente)
        folder = FolderBlock.unpack(file.read(FolderBlock.SIZE))
        siguiente = folder.b_content[0].b_inodo
        file.seek(siguiente)
        ubicacion_inodo_users = siguiente
        inodo = Inode.unpack(file.read(Inode.SIZE))
        primerbloque = -1
        cont = 0
        texto = ""
        for i,item in enumerate(inodo.i_block[:12]):
            if item != -1 and i == 0:
                primerbloque = item
            if item != -1:
                cont = i+1
                siguiente = item
                file.seek(siguiente)
                fileblock = FileBlock.unpack(file.read(FileBlock.SIZE))
                texto += fileblock.b_content.rstrip('\x00')
        indice_a_borrar = (primerbloque- superblock.s_block_start)//64   
        grupos = parse_users(texto)
        
        #user = user[:10]
        #password = password[:10]
        #group = group[:10]
        #print("ESTE ES EL GRUPO QUE SE VA A CREAR")
        #print("usuario a buscar___")
        #print(user)
        #print("grupos____")
        #print(grupos)
        group_exists = False  # Initially, we assume the group does not exist
        for n in grupos:
            #print (n)
            #print(user)
            if user in n:
                print("Error: The user already exists.*********************************************************************")
                return
        #
        grupos22 = extract_active_groups(texto)
        group_exists2 = False  # Initially, we assume the group does not exist
        for n2 in grupos22:
            # Check if the group exists in current item
            if n2['groupname'] == group:
                group_exists2 = True
                break

        if group_exists2==False:
            print(f"Error: The group {group} doesn't exists.")
            return
        #

             
        
            
        #print("ESTE ES EL USUARIO QUE SE VA A CREAR")
        id = get_group_id(group,grupos22 )
        #texto+='2,G,usuarios\n2,U,usuarios,user1,usuario\n'
        texto += f'{id},U,{group},{user},{password}\n'
        length = len(texto)
        fileblocks = length//64
        if length%64 != 0:
            fileblocks += 1
        bitmap_bloques_inicio = superblock.s_bm_block_start
        cantidad_bloques = superblock.s_blocks_count
        FORMAT = f'{cantidad_bloques}s'
        SIZE = struct.calcsize(FORMAT)
        file.seek(bitmap_bloques_inicio)
        bitmap_bloques = struct.unpack(FORMAT, file.read(SIZE))
        bitmap=bitmap_bloques[0].decode('utf-8')
        #print(bitmap)
                    
        if fileblocks<=12:
            bitmap = bitmap[:indice_a_borrar] + '0'*cont + bitmap[indice_a_borrar+cont:]
            index = bitmap.find('0'*fileblocks)
            #print(bitmap)
            a = bitmap[:index] + '1'*fileblocks + bitmap[index+fileblocks:]
            #print(a)
            chunks = [texto[i:i+64] for i in range(0, len(texto), 64)]
            for i,n in enumerate(chunks):
                new_fileblock = FileBlock()
                new_fileblock.b_content = n
                inodo.i_block[i] = primerbloque+i*64
                file.seek(primerbloque+i*64)
                file.write(new_fileblock.pack())
            #rewriteinode
            file.seek(ubicacion_inodo_users)
            file.write(inodo.pack())
            #rewrite bitmap
            file.seek(bitmap_bloques_inicio)
            file.write(a.encode('utf-8'))
            return
                        

                    
                        
#write a storu about                     
def makegroup(params, mounted_partitions,id):
    print(f'👩‍👨‍👧‍👧 <<RUNNING MAKE-GROUP {params} _ _ _ _ _ _ _ _ _ ')
    if id == None:
        print("Error: The id is required.")
        return
    try: 
        group = params['name']
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
        file.seek(superblock.s_inode_start)
        inodo = Inode.unpack(file.read(Inode.SIZE))
        siguiente = inodo.i_block[0]
        file.seek(siguiente)
        folder = FolderBlock.unpack(file.read(FolderBlock.SIZE))
        siguiente = folder.b_content[0].b_inodo
        file.seek(siguiente)
        ubicacion_inodo_users = siguiente
        inodo = Inode.unpack(file.read(Inode.SIZE))
        primerbloque = -1
        cont = 0
        texto = ""
        for i,item in enumerate(inodo.i_block[:12]):
            if item != -1 and i == 0:
                primerbloque = item
            if item != -1:
                cont = i+1
                siguiente = item
                file.seek(siguiente)
                fileblock = FileBlock.unpack(file.read(FileBlock.SIZE))
                texto += fileblock.b_content.rstrip('\x00')
        indice_a_borrar = (primerbloque- superblock.s_block_start)//64   
        grupos = extract_active_groups(texto)
        group_exists = False  # Initially, we assume the group does not exist
        for n in grupos:
            # Check if the group exists in current item
            if n['groupname'] == group:
                group_exists = True
                break

        if group_exists==True:
            print(f"Error: The group {group} already exist.")
            return

        #print("ESTE ES EL GRUPO QUE SE VA A CREAR")
        #print(group)
        #print(grupos)
        max_id = max(g['id'] for g in grupos)
        
        # The next available ID will be max_id + 1
        next_id = max_id + 1
        #print(next_id)
        texto += f'{next_id},G,{group}\n'
        #print(texto)
        length = len(texto)
        fileblocks = length//64
        if length%64 != 0:
            fileblocks += 1
        bitmap_bloques_inicio = superblock.s_bm_block_start
        cantidad_bloques = superblock.s_blocks_count
        FORMAT = f'{cantidad_bloques}s'
        SIZE = struct.calcsize(FORMAT)
        file.seek(bitmap_bloques_inicio)
        bitmap_bloques = struct.unpack(FORMAT, file.read(SIZE))
        bitmap=bitmap_bloques[0].decode('utf-8')
        #print(bitmap)
                    
        if fileblocks<=12:
            bitmap = bitmap[:indice_a_borrar] + '0'*cont + bitmap[indice_a_borrar+cont:]
            index = bitmap.find('0'*fileblocks)
            #print(bitmap)
            a = bitmap[:index] + '1'*fileblocks + bitmap[index+fileblocks:]
            #print(a)
            chunks = [texto[i:i+64] for i in range(0, len(texto), 64)]
            for i,n in enumerate(chunks):
                new_fileblock = FileBlock()
                new_fileblock.b_content = n
                inodo.i_block[i] = primerbloque+i*64
                file.seek(primerbloque+i*64)
                file.write(new_fileblock.pack())
            #rewriteinode
            file.seek(ubicacion_inodo_users)
            file.write(inodo.pack())
            #rewrite bitmap
            file.seek(bitmap_bloques_inicio)
            file.write(a.encode('utf-8'))
            print(f"Group {group} was created successfully.")
            return
        
        
        
def remgroup(params, mounted_partitions,id):
    print(f'🙅‍♂️ <<RUNNING REMOVE-GROUP {params} _ _ _ _ _ _ _ _ _ ')
    if id == None:
        print("Error: The id is required.")
        return
    try: 
        group = params['name']
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
        file.seek(superblock.s_inode_start)
        inodo = Inode.unpack(file.read(Inode.SIZE))
        siguiente = inodo.i_block[0]
        file.seek(siguiente)
        folder = FolderBlock.unpack(file.read(FolderBlock.SIZE))
        siguiente = folder.b_content[0].b_inodo
        file.seek(siguiente)
        ubicacion_inodo_users = siguiente
        inodo = Inode.unpack(file.read(Inode.SIZE))
        primerbloque = -1
        cont = 0
        texto = ""
        for i,item in enumerate(inodo.i_block[:12]):
            if item != -1 and i == 0:
                primerbloque = item
            if item != -1:
                cont = i+1
                siguiente = item
                file.seek(siguiente)
                fileblock = FileBlock.unpack(file.read(FileBlock.SIZE))
                texto += fileblock.b_content.rstrip('\x00')
        indice_a_borrar = (primerbloque- superblock.s_block_start)//64   
        grupos = extract_active_groups(texto)
        group_exists = False  # Initially, we assume the group does not exist
        for n in grupos:
            # Check if the group exists in current item
            if n['groupname'] == group:
                group_exists = True
                break

        if group_exists==False:
            print(f"Error: The group {group} doesn´t exists.")
            return
        arreglo = texto.split('\n')
        lineas = []
        for i,n in enumerate(arreglo):
            if n == '':
                continue
            linea = n.split(',')
            if linea[1] == 'G' and linea[2] == group:
                linea[0] = '0'
            lineas.append(','.join(linea))
            print(lineas)
        texto = '\n'.join(lineas)
        texto+='\n'
        print(texto)
        #print(texto.split('\n'))
        length = len(texto)
        fileblocks = length//64
        if length%64 != 0:
            fileblocks += 1
        bitmap_bloques_inicio = superblock.s_bm_block_start
        cantidad_bloques = superblock.s_blocks_count
        FORMAT = f'{cantidad_bloques}s'
        SIZE = struct.calcsize(FORMAT)
        file.seek(bitmap_bloques_inicio)
        bitmap_bloques = struct.unpack(FORMAT, file.read(SIZE))
        bitmap=bitmap_bloques[0].decode('utf-8')
        #print(bitmap)
                    
        if fileblocks<=12:
            bitmap = bitmap[:indice_a_borrar] + '0'*cont + bitmap[indice_a_borrar+cont:]
            index = bitmap.find('0'*fileblocks)
            #print(bitmap)
            a = bitmap[:index] + '1'*fileblocks + bitmap[index+fileblocks:]
            #print(a)
            chunks = [texto[i:i+64] for i in range(0, len(texto), 64)]
            for i,n in enumerate(chunks):
                new_fileblock = FileBlock()
                new_fileblock.b_content = n
                inodo.i_block[i] = primerbloque+i*64
                file.seek(primerbloque+i*64)
                file.write(new_fileblock.pack())
            #rewriteinode
            file.seek(ubicacion_inodo_users)
            file.write(inodo.pack())
            #rewrite bitmap
            file.seek(bitmap_bloques_inicio)
            file.write(a.encode('utf-8'))
            return

def remuser(params, mounted_partitions,id):   
    print(f'🙅‍♂️ <<RUNNING REMOVE-USER {params} _ _ _ _ _ _ _ _ _ ')
    #print(params)
    if id == None:
        print("Error: The id is required.")
        return
    try: 
        user = params['user']
    except:
        print("Error: The user is required required.")
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
        file.seek(superblock.s_inode_start)
        inodo = Inode.unpack(file.read(Inode.SIZE))
        siguiente = inodo.i_block[0]
        file.seek(siguiente)
        folder = FolderBlock.unpack(file.read(FolderBlock.SIZE))
        siguiente = folder.b_content[0].b_inodo
        file.seek(siguiente)
        ubicacion_inodo_users = siguiente
        inodo = Inode.unpack(file.read(Inode.SIZE))
        primerbloque = -1
        cont = 0
        texto = ""
        for i,item in enumerate(inodo.i_block[:12]):
            if item != -1 and i == 0:
                primerbloque = item
            if item != -1:
                cont = i+1
                siguiente = item
                file.seek(siguiente)
                fileblock = FileBlock.unpack(file.read(FileBlock.SIZE))
                texto += fileblock.b_content.rstrip('\x00')
        indice_a_borrar = (primerbloque- superblock.s_block_start)//64   
        grupos = parse_users(texto)

        group_exists = False  # Initially, we assume the group does not exist
        bandera = False
        for n in grupos:
            if user in n:
                bandera = True
                break
        if bandera == False:
            print(f"Error: The user doesn´t exists.")
            return
        arreglo = texto.split('\n')
        lineas = []
        for i,n in enumerate(arreglo):
            if n == '':
                continue
            linea = n.split(',')
            if linea[1] == 'U' and linea[3] == user:
                linea[0] = '0'
            lineas.append(','.join(linea))
            #print(lineas)
        texto = '\n'.join(lineas)
        texto+='\n'
        #print(texto)
        #print(texto.split('\n'))
        length = len(texto)
        fileblocks = length//64
        if length%64 != 0:
            fileblocks += 1
        bitmap_bloques_inicio = superblock.s_bm_block_start
        cantidad_bloques = superblock.s_blocks_count
        FORMAT = f'{cantidad_bloques}s'
        SIZE = struct.calcsize(FORMAT)
        file.seek(bitmap_bloques_inicio)
        bitmap_bloques = struct.unpack(FORMAT, file.read(SIZE))
        bitmap=bitmap_bloques[0].decode('utf-8')
        #print(bitmap)
                    
        if fileblocks<=12:
            bitmap = bitmap[:indice_a_borrar] + '0'*cont + bitmap[indice_a_borrar+cont:]
            index = bitmap.find('0'*fileblocks)
            #print(bitmap)
            a = bitmap[:index] + '1'*fileblocks + bitmap[index+fileblocks:]
            #print(a)
            chunks = [texto[i:i+64] for i in range(0, len(texto), 64)]
            for i,n in enumerate(chunks):
                new_fileblock = FileBlock()
                new_fileblock.b_content = n
                inodo.i_block[i] = primerbloque+i*64
                file.seek(primerbloque+i*64)
                file.write(new_fileblock.pack())
            #rewriteinode
            file.seek(ubicacion_inodo_users)
            file.write(inodo.pack())
            #rewrite bitmap
            file.seek(bitmap_bloques_inicio)
            file.write(a.encode('utf-8'))
            #print(a)
            print(f"User {user} was removed successfully.")
            return