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
from mkfile import busca
from mkfs import parse_users
from mountingusers import extract_active_groups, get_group_id

def read_file_inode(file, lista):
    texto = ''
    for n in lista:
        if n == -1:
            continue
        file.seek(n)
        fileblock = FileBlock.unpack(file.read(FileBlock.SIZE))
        texto += fileblock.b_content.rstrip('\x00')
    return texto
def cambiar_id_inodos_recursivamente(file,byte, tipo, id):
    if tipo == 0:
        file.seek(byte)
        inodo = Inode.unpack(file.read(Inode.SIZE))
        inodo.i_uid = id
        inodo.I_gid = id
        file.seek(byte)
        file.write(inodo.pack())
        if inodo.i_type == '1':
            return
        for n in inodo.i_block:
            if n != -1:
                cambiar_id_inodos_recursivamente(file,n,1,id)
    if tipo == 1:
        file.seek(byte)
        bloque = FolderBlock.unpack(file.read(FolderBlock.SIZE))
        for n in bloque.b_content:
            if n.b_inodo != -1:
                cambiar_id_inodos_recursivamente(file,n.b_inodo,0,id)
def cambiar_permiso_inodos_recursivamente(file,byte, tipo, permiso):
    if tipo == 0:
        file.seek(byte)
        inodo = Inode.unpack(file.read(Inode.SIZE))
        inodo.i_perm = permiso
        file.seek(byte)
        file.write(inodo.pack())
        if inodo.i_type == '1':
            return
        for n in inodo.i_block:
            if n != -1:
                cambiar_permiso_inodos_recursivamente(file,n,1,permiso)
    if tipo == 1:
        file.seek(byte)
        bloque = FolderBlock.unpack(file.read(FolderBlock.SIZE))
        for n in bloque.b_content:
            if n.b_inodo != -1:
                cambiar_permiso_inodos_recursivamente(file,n.b_inodo,0,permiso)
def change_group_user(text, new_id, new_group_name, name):
    # Splitting the text into lines
    lines = text.strip().split('\n')
    
    # First, we modify the group ID of the user
    for idx, line in enumerate(lines):
        parts = line.split(',')
        if parts[1] == 'U' and parts[3] == name:
            parts[0] = str(new_id)
            parts[2] = new_group_name
            lines[idx] = ','.join(parts)
            break
    
    # Then, we reorder the text
    groups = {}
    users = {}
    disabled_users = []  # Users with ID 0
    
    for line in lines:
        parts = line.split(',')
        if parts[1] == 'G':
            groups[parts[0]] = line
            users[parts[0]] = []
        elif parts[1] == 'U':
            if parts[0] == '0':
                disabled_users.append(line)
            else:
                if parts[0] not in users:
                    users[parts[0]] = []
                users[parts[0]].append(line)
    
    # Reconstructing the text
    sorted_lines = []
    for gid, group in groups.items():
        sorted_lines.append(group)
        sorted_lines.extend(users.get(gid, []))
    
    # Append disabled users at the end
    sorted_lines.extend(disabled_users)
    
    return '\n'.join(sorted_lines)

        
def count_occupied_blocks_in_inode(inodo):
    count = 0
    for n in inodo.i_block:
        if n != -1:
            count += 1
    return count
def count_bloques_for_a_text(text):
    length = len(text)
    fileblocks = length//64
    if length%64 != 0:
        fileblocks += 1
    return fileblocks
        
def chown(params, mounted_partitions,id, usuario_actual):  
    print(f'🤝<<RUNNING CHOWN {params}_ _ _ _ _ _ _ _ _ ')
    if id == None:
        print("Error: The id is required.")
        return
    try: 
        insidepath = params['path']
        user = params['user']
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
        file.seek(PI)
        
        inodo = Inode.unpack(file.read(Inode.SIZE))
        if str(inodo.i_uid) != str(usuario_actual['id']):
            print(f'No tiene permisos para cambiar el propietario del archivo {insidepath}')
            return
        
        _,PI_users = busca(file,superblock.s_inode_start,0,'users.txt')
        file.seek(PI_users)
        inodo_archivo = Inode.unpack(file.read(Inode.SIZE))
        texto_usuarios = read_file_inode(file, inodo_archivo.i_block)
        print(texto_usuarios)
        grupos = parse_users(texto_usuarios)
        usuario_obtenido = None
        for n in grupos:
            if user in n:
                usuario_obtenido = n
                break
        print(usuario_obtenido)
        
        if usuario_obtenido:
            inodo.i_uid = int(usuario_obtenido[user]['id'])
            inodo.I_gid = int(usuario_obtenido[user]['id'])
            file.seek(PI)
            file.write(inodo.pack())
            print(f'El propietario del archivo {insidepath} ha sido cambiado a {user}')
            r = params.get('r', '/')
            if r == '-r':
                cambiar_id_inodos_recursivamente(file,PI,0,inodo.i_uid)
            
def chgrp(params, mounted_partitions,id, usuario_actual):  
    print(f'👷<<- - - - - - -CHGRP {params}')
    if id == None:
        print("Error: The id is required.")
        return
    try: 
        user = params['user']
        group = params['grp']
        
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
        
        
        PI = superblock.s_inode_start
        _,PI_users = busca(file,PI,0,'users.txt')
        file.seek(PI_users)
        inodo_archivo = Inode.unpack(file.read(Inode.SIZE))
        texto_usuarios = read_file_inode(file, inodo_archivo.i_block)
        group_id = get_group_id( group,extract_active_groups(texto_usuarios))
        usuario_existe = False
        for n in parse_users(texto_usuarios):
            if user in n:
                usuario_existe = True
                break
        if not usuario_existe:
            print(f'🚷🚷__El usuario {user} no existe')
            return
        if group_id == None:
            print(f'🚷🚷__El grupo {group} no existe')
            return
        new_texto = change_group_user(texto_usuarios, group_id,group , user) + '\n'
        cantidad_bloques_utilizados = count_occupied_blocks_in_inode(inodo_archivo)
        cantitda_bloques_por_utilizat = count_bloques_for_a_text(new_texto)
        bitmap_bloques_inicio = superblock.s_bm_block_start
        cantidad_bloques = superblock.s_blocks_count
        FORMAT = f'{cantidad_bloques}s'
        SIZE = struct.calcsize(FORMAT)
        file.seek(bitmap_bloques_inicio)
        bitmap_bloques = struct.unpack(FORMAT, file.read(SIZE))
        bitmap=bitmap_bloques[0].decode('utf-8')
        primerbloque = inodo_archivo.i_block[0]
        indice_a_borrar = (primerbloque-superblock.s_block_start)//64
        if cantitda_bloques_por_utilizat<=12:
            print(f'cantidad de bloques utilizados {cantidad_bloques_utilizados}')
            print(f'cantidad de bloques por utilizar {cantitda_bloques_por_utilizat}')
            #print(f'{new_texto} sigue')
            tupu = new_texto[-1]=="\n"
            print(f'{tupu}')
            input('__verificar chgrp_')
            bitmap = bitmap[:indice_a_borrar] + '0'*cantidad_bloques_utilizados + bitmap[indice_a_borrar+cantidad_bloques_utilizados:]
            index = bitmap.find('0'*cantitda_bloques_por_utilizat)
            a = bitmap[:index] + '1'*cantitda_bloques_por_utilizat + bitmap[index+cantitda_bloques_por_utilizat:]
            #print(a)
            texto = new_texto
            chunks = [texto[i:i+64] for i in range(0, len(texto), 64)]
            for i,n in enumerate(chunks):
                new_fileblock = FileBlock()
                new_fileblock.b_content = n
                inodo_archivo.i_block[i] = primerbloque+i*64
                file.seek(primerbloque+i*64)
                file.write(new_fileblock.pack())
            file.seek(PI_users)
            file.write(inodo_archivo.pack())
            file.seek(bitmap_bloques_inicio)
            file.write(struct.pack(FORMAT,a.encode('utf-8')))
            print(f'✅✅__El grupo del usuario {user} ha sido cambiado a {group}')
        
        
def chmod(params, mounted_partitions,id, usuario_actual):  
    print(f'🔨<<RUNNING CHMOD {params}_ _ _ _ _ _ _ _ _ ')
    if id == None:
        print("Error: The id is required.")
        return
    try: 
        insidepath = params['path']
        ugo = params['ugo']
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
        permisos_existentes = ['664','777','000','111','222','333','444','555','666']
        if str(ugo) not in permisos_existentes:
            print(f'🚷🚷__El permiso {ugo} no existe')
            return
        file.seek(PI)
        inodo = Inode.unpack(file.read(Inode.SIZE))
        inodo.i_perm = int(ugo)
        file.seek(PI)
        file.write(inodo.pack())
        print(f'El propietario del archivo {insidepath} ha sido cambiado a {ugo}')
        r = params.get('r', '/')
        if r == '-r':
            cambiar_permiso_inodos_recursivamente(file,PI,0,inodo.i_perm)