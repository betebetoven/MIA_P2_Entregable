from ply.lex import lex
from ply.yacc import yacc

from mkdisk import mkdisk, rmdisk, fdisk
from comandos import comandos
from mount import mount, unmount
from mkfs import mkfs, login, makeuser, makegroup, remgroup, remuser
from FORMATEO.ext2.ext2 import Superblock, Inode, FolderBlock, FileBlock, PointerBlock, block, Content, Journal
from mkfile import mkfile, cat, remove, rename, copy, move, find
from permisos import chown, chgrp,chmod
from journal import add_to_journal, ver_journal_actual, loss
from rep import rep
import struct
import os
from MBR import MBR
from prettytable import PrettyTable
from send import printt
mapa_de_bytes = []
contador_historial_mapa_de_bytes= 0
def ver_bitmaps(instruccion, mounted_partitions, id):
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
        #ver bitmaps
        print("Bitmap de inodos")
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
        texto =f'\nInstruccion: {instruccion.upper()}'
        texto +="\n______ESTADO BITMAPS______"
        texto +="\nbloques"
        texto +="\n"+bitmap_bloques
        texto +="\ninodos"
        texto +="\n"+bitmap_inodos
        texto +="\n______FIN ESTADO BITMAPS______"
        global contador_historial_mapa_de_bytes
        inodo_dot = generate_dot(instruccion,bitmap_inodos, "inodo", contador_historial_mapa_de_bytes)
        bloque_dot = generate_dot(instruccion,bitmap_bloques, "bloque", contador_historial_mapa_de_bytes)
        global mapa_de_bytes
        mapa_de_bytes.append((inodo_dot, bloque_dot))
        contador_historial_mapa_de_bytes += 1
import math

def generate_dot(instruccion, bitmap, label, contador):
    bitmap = bitmap[:100]
    length = len(bitmap)
    rows = math.ceil(math.sqrt(length))
    
    # Split the bitmap string into rows
    split_bitmap = [bitmap[i:i+rows] for i in range(0, length, rows)]
    
    # Join the split rows with <br> tags
    formatted_bitmap = '\\n'.join(split_bitmap)
    #dot_string += f'label="gg";\n'
    
    # Use the formatted bitmap in the label of the node
    dot_string = f'{label}_{contador} [shape=box,  label="{instruccion}\n{formatted_bitmap}"];\n'
    
    return dot_string
import ast
mounted_partitions = []
users=None
current_partition = None
def recuperar(params, mounted_partitions, usuario_actual_boluo):
    print(f'🚑 <<RUNNING RECOVERY {params} _ _ _ _ _ _ _ _ _ ')
    global users
    global current_partition
    id = params.get('id', None)
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
    #write null bytes all over the partition
    filename = path
    current_directory = os.getcwd()
    full_path= f'{current_directory}/discos_test{filename}'
    if not os.path.exists(full_path):
        print(f"Error: The file {full_path} does not exist.")
        return
    with open(full_path, "rb+") as file:
        try: 
            file.seek(inicio+Superblock.SIZE)
            journal = Journal.unpack(file.read(Journal.SIZE))
        except:
            printt("🚷🚷: The journal does not exist we are on a ext2")
            return
        content = journal.journal_data
        commands = [ast.literal_eval(line) for line in content.split("\n") if line.strip()]
        print(commands)
        for n in commands:
            if n[0] == 'mkfs':
                mkfs(n[1], mounted_partitions, users)
            elif n[0] == 'login':
                users, current_partition = login(n[1], mounted_partitions)
            elif n[0]=='mkusr':
                if users != None and users['username']=='root' :
                    makeuser(n[1], mounted_partitions, current_partition)
                    
                else:
                    printt("🚷🚷: You must be logged in as root to use this command")
            elif n[0]=='mkgrp':
                if users != None and users['username']=='root' :
                    makegroup(n[1], mounted_partitions, current_partition)
            
                else:
                    printt("🚷🚷: You must be logged in as root to use this command")
            elif n[0]=='rmusr':
                if users != None and users['username']=='root' :
                    remuser(n[1], mounted_partitions, current_partition)
                else:
                    printt("🚷🚷: You must be logged in as root to use this command")
            elif n[0]=='rmgrp':
                if users != None and users['username']=='root' :
                    remgroup(n[1], mounted_partitions, current_partition)
                else:
                    printt("🚷🚷: You must be logged in as root to use this command")
            elif n[0]=='mkfile':
                if users != None:
                    mkfile(n[1], mounted_partitions, current_partition, users)
                else:
                    printt("🚷🚷: You must be logged in as root to use this command")
            elif n[0]=='remove':
                if users != None:
                    remove(n[1], mounted_partitions, current_partition, users)
                else:
                    printt("🚷🚷: You must be logged in to use this command")
            elif n[0]=='rename':
                if users != None:
                    rename(n[1], mounted_partitions, current_partition, users)
                else:
                    printt("🚷🚷: You must be logged in to use this command")
            elif n[0]=='edit':
                if users != None:
                    remove(n[1], mounted_partitions, current_partition, users)
                    mkfile(n[1], mounted_partitions, current_partition, users)
                else:
                    printt("🚷🚷: You must be logged in to use this command")
            elif n[0]=='copy':
                if users != None:
                    copy(n[1], mounted_partitions, current_partition, users)
                else:
                    printt("🚷🚷: You must be logged in to use this command")
            elif n[0]=='move':
                if users != None:
                    move(n[1], mounted_partitions, current_partition, users)
                    
                else:
                    printt("🚷🚷: You must be logged in to use this command")
            elif n[0]=='chown':
                if users != None:
                    chown(n[1], mounted_partitions, current_partition, users)
                else:
                    printt("🚷🚷: You must be logged in to use this command")
            elif n[0]=='chgrp':
                if users != None and users['username']=='root' :
                    chgrp(n[1], mounted_partitions, current_partition, users)
                    
                else:
                    printt("🚷🚷: You must be logged in as root to use this command")
            elif n[0]=='chmod':
                if users != None and users['username']=='root' :
                    chmod(n[1], mounted_partitions, current_partition, users)
                else:
                    printt("🚷🚷: You must be logged in to use this command")
        ver_bitmaps("recuperar"+str(params), mounted_partitions, id)       
                
                
                

# --- Tokenizer

# All tokens must be named in advance.
tokens = ( 'MKDISK', 'SIZE', 'PATH', 'UNIT', 'FIT','ENCAJE',  
          'NAME',  
          'NOMBRE', 
          'NOMBREFEA',
          'UNIDAD', 
          'DIRECCION',
          'DIRECCIONFEA', 
          'NUMERO' , 
          'RMDISK',
          'FDISK',
          'TYPE',
          'TIPO',
          'DELETE',
          'DELETO',
          'ADD',
          'MOUNT',
          'ID',
          'IDENTIFICADOR',
          'UNMOUNT',
          'MKFS',
          'LOGIN',
          'USER',
          'PASSWORD',
          'CONTRA',
          'CONTRAFEA',
          'LOGOUT',
          'MKUSR', 
          'GRP',
          'MKGRP',
          'RMGRP',
          'RMUSR',
          'MKFILE',
          'MENOSR',
          'CONT',
          'CAT',
          'FILE1',
          'FILE2',
          'FILE3',
          'FILE4',
          'REMOVE',
          'RENAME',
          'EDIT',
          'COPY',
          'DESTINO',
          'MOVE',
          'FIND',
          'PAUSE',
          'CHOWN',
          'CHGRP',
          'UGO',
          'CHMOD',
          'FS',
          'LOSS',
          'RECOVERY',
          'REP',
          'RUTA',
          'COMENTARIO',)

# Ignored characters
t_ignore = ' \t'

# Token matching rules are written as regexs

t_MKDISK = r'mkdisk'
t_MKFS = r'mkfs'
t_RMDISK = r'rmdisk'
t_FDISK = r'fdisk'
t_MOUNT = r'mount'
t_UNMOUNT = r'unmount'
t_LOGIN = r'login'
t_LOGOUT = r'logout'
t_MKUSR = r'mkusr'
t_MKGRP = r'mkgrp'
t_RMGRP = r'rmgrp'
t_RMUSR = r'rmusr'
t_MKFILE = r'mkfile|mkdir'
t_CAT = r'cat'
t_REMOVE = r'remove'
t_RENAME = r'rename'
t_EDIT = r'edit'
t_COPY = r'copy'
t_MOVE = r'move'
t_FIND = r'find'
t_PAUSE = r'pause'
t_CHOWN = r'chown'
t_CHGRP = r'chgrp'
t_CHMOD = r'chmod'
t_LOSS = r'loss'
t_RECOVERY = r'recovery'
t_REP = r'rep'

t_USER = r'-user'
t_PASSWORD = r'-pass'
t_GRP = r'-grp'
t_NAME = r'-name'
t_ID = r'-id'
t_CONT = r'-cont='
t_FILE1 = r'-file1='
t_FILE2 = r'-file2='
t_FILE3 = r'-file3='
t_FILE4 = r'-file4='
t_DESTINO = r'-destino='
t_FS = r'-fs'

t_SIZE = r'-size='
t_UGO = r'-ugo='
t_PATH = r'-path='
t_RUTA = r'-Ruta='
t_UNIT = r'-unit='
t_FIT = r'-fit='
t_TYPE = r'-type='
t_DELETE = r'-delete='
t_ADD = r'-add='




# A function can be used if there is an associated action.
# Write the matching regex in the docstring.
def t_COMENTARIO(t):
    r'\#.*[\n]'
    pass

def t_NUMERO(t):
    r'-?\d+'
    t.value = int(t.value)
    return t

def t_DIRECCION(t):
    r'/[a-zA-Z0-9_\\/:.-]+(.dsk|.txt)?'
    return t
def t_DIRECCIONFEA(t):
    r'"/[a-zA-Z0-9_\\/:. -]+(.dsk|.txt)?"'
    t.value = t.value[1:-1]  # Strip the double quotes
    return t


def t_TIPO(t):
    r'(P|E|L)'
    return t
def t_DELETO(t):
    r'(FULL|full)'
    return t
    
def t_ENCAJE(t):
    r'(BF|FF|WF)'
    return t
def t_UNIDAD(t):
    r'(K|M|B)'
    return t
def t_NOMBRE(t):
    r'=[a-zA-Z_\*\?][a-zA-Z0-9_]*(.txt)?'
    t.value = t.value[1:]  # remove the '=' at the beginning
    return t
def t_NOMBREFEA(t):
    r'="[a-zA-Z_][a-zA-Z0-9_ ]*(.txt)?"'
    t.value = t.value[2:-1]  # remove the '=' at the beginning
    return t
def t_IDENTIFICADOR(t):
    r'=[0-9][0-9][0-9][a-zA-Z0-9_]+'
    t.value = t.value[1:]
    return t

def t_CONTRA(t):
    r'=[a-zA-Z0-9]+'
    t.value = t.value[1:]
    return t
def t_CONTRAFEA(t):
    r'="[a-zA-Z0-9]+"'
    t.value = t.value[2:-1]
    return t
def t_MENOSR(t):
    r'-r'
    return t


# Ignored token with an action associated with it
def t_ignore_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count('\n')

# Error handler for illegal characters
def t_error(t):
    print(f'Illegal character {t.value[0]!r}')
    t.lexer.skip(1)

# Build the lexer object
lexer = lex()
    
# --- Parser

# Write functions for each grammar rule which is
# specified in the docstring.


def p_command_list(p):
    '''command_list : expression
                    | command_list expression'''
    if len(p) == 3:
        comandos = p[1]
        comandos.append(p[2])
        p[0] = comandos
    else:
        comandos = []
        comandos.append(p[1])
        p[0] = comandos




def p_expression(p):
    '''
    expression : mkdisk
                | rmdisk
                | fdisk
                | mount
                | unmount
                | mkfs
                | login
                | logout
                | mkusr
                | mkgrp
                | rmgrp
                | rmusr
                | mkfile
                | cat
                | remove
                | rename
                | edit
                | copy
                | move
                | find
                | pause
                | chown
                | chgrp
                | chmod
                | loss
                | recovery
                | rep
                
    '''
    #if p[1] type string then p[0] = p[1]
    #printt("            "+str(p[1]))
    p[0] = p[1]
    

########################PARAMETROOOOOOOOOOOOOOOOOOOOOOOSSSSS
def p_name(p):
    '''
    nament : NAME NOMBRE
    '''
    p[0] = ('name', p[2])
def p_name2(p):
    '''
    nament : NAME NOMBREFEA
    '''
    p[0] = ('name', p[2])
def p_user(p):
    '''
    usernt : USER NOMBRE
    '''
    p[0] = ('user', p[2])
def p_user2(p):
    '''
    usernt : USER NOMBREFEA
    '''
    p[0] = ('user', p[2])
def p_fs(p):
    '''
    fsnt : FS NOMBRE
    '''
    p[0] = ('fs', p[2])
def p_grp(p):
    '''
    grpnt : GRP NOMBRE
    '''
    p[0] = ('grp', p[2])
def p_grp2(p):
    '''
    grpnt : GRP NOMBREFEA
    '''
    p[0] = ('grp', p[2])
def p_password(p):
    '''
    passnt : PASSWORD CONTRA
    '''
    p[0] = ('pass', p[2])
def p_password2(p):
    '''
    passnt : PASSWORD CONTRAFEA
    '''
    p[0] = ('pass', p[2])
def p_password3(p):
    '''
    passnt : PASSWORD NOMBRE
    '''
    p[0] = ('pass', p[2])
def p_password4(p):
    '''
    passnt : PASSWORD NOMBREFEA
    '''
    p[0] = ('pass', p[2])
def p_size(p):
    '''
    sizent : SIZE NUMERO
    '''
    p[0] = ('size', p[2])
def p_ugo(p):
    '''
    ugont : UGO NUMERO
    '''
    p[0] = ('ugo', p[2])
def p_path(p):
    '''
    pathnt : PATH DIRECCION
    '''
    p[0] = ('path', p[2])    
def p_cont(p):
    '''
    contnt : CONT DIRECCION
    '''
    p[0] = ('cont', p[2])
def p_cont2(p):
    '''
    contnt : CONT DIRECCIONFEA
    '''
    p[0] = ('cont', p[2])
def p_file1(p):
    '''
    file1nt : FILE1 DIRECCION
    '''
    p[0] = ('file1', p[2])
def p_file2(p):
    '''
    file2nt : FILE2 DIRECCION
    '''
    p[0] = ('file2', p[2])
def p_file3(p):
    '''
    file3nt : FILE3 DIRECCION
    '''
    p[0] = ('file3', p[2])
def p_file4(p):
    '''
    file4nt : FILE4 DIRECCION
    '''
    p[0] = ('file4', p[2])
def p_fil12(p):
    '''
    file1nt : FILE1 DIRECCIONFEA
    '''
    p[0] = ('file1', p[2])
def p_file22(p):
    '''
    file2nt : FILE2 DIRECCIONFEA
    '''
    p[0] = ('file2', p[2])
def p_file32(p):
    '''
    file3nt : FILE3 DIRECCIONFEA
    '''
    p[0] = ('file3', p[2])
def p_file42(p):
    '''
    file4nt : FILE4 DIRECCIONFEA
    '''
    p[0] = ('file4', p[2])
def p_tipo(p):
    '''
    typent : TYPE TIPO
    '''
    p[0] = ('type', p[2])
def p_tipo2(p):
    '''
    typent : TYPE DELETO
    '''
    p[0] = ('type', p[2])    
def p_delete(p):
    '''
    deletent : DELETE DELETO
    '''
    p[0] = ('delete', p[2])
def p_add(p):
    '''
    addnt : ADD NUMERO
    '''
    p[0] = ('add', p[2])
def p_path2(p):
    '''
    pathnt : PATH DIRECCIONFEA
    '''
    p[0] = ('path', p[2])
def p_ruta(p):
    '''
    rutant : RUTA DIRECCION
    '''
    p[0] = ('ruta', p[2])
def p_ruta2(p):
    '''
    rutant : RUTA DIRECCIONFEA
    '''
    p[0] = ('ruta', p[2])
def p_destino(p):
    '''
    destint : DESTINO DIRECCION
    '''
    p[0] = ('destino', p[2])
def p_destino2(p):
    '''
    destint : DESTINO DIRECCIONFEA
    '''
    p[0] = ('destino', p[2])
def p_unit(p):
    '''
    unitnt : UNIT UNIDAD
    '''
    p[0] = ('unit', p[2])    
def p_fit(p):
    '''
    fitnt : FIT ENCAJE
    '''
    p[0] = ('fit', p[2])
def p_id(p):
    '''
    idnt : ID IDENTIFICADOR
    '''
    p[0] = ('id', p[2])
def p_menosr(p):
    '''
    rnt : MENOSR
    '''
    p[0] = ('r', p[1])

def p_param(p):
    '''
    param : sizent
          | pathnt
          | unitnt
          | fitnt
          | nament
          | typent
          | deletent
          | addnt
          | idnt
          | usernt
          | passnt
          | grpnt
          | rnt
          | contnt
          | file1nt
          | file2nt
          | file3nt
          | file4nt
          | destint
          | ugont
          | fsnt
          | rutant
            
          
            
    '''
    p[0] = p[1]    
def p_params(p):
    '''
    params : params param
           | param
    '''
    if len(p) == 3:
        p[0] = {**p[1], p[2][0]: p[2][1]}
    else:
        p[0] = {p[1][0]: p[1][1]}
#################################################FIN DE PARAMETROOOOOOOOOOOOSSSSSSSSSSSSSS
    
    
def p_mkdisk(p):
    '''
    mkdisk : MKDISK params
    '''
    #CREATE BINARY FILE
    mkdisk(p[2])
    p[0] = ('mkdisk', p[2])
    
def p_rmdisk(p):
    '''
    rmdisk : RMDISK params
    '''
    rmdisk(p[2])
    p[0] = ('rmdisk', p[2])

def p_fdisk(p):
    '''
    fdisk : FDISK params
    '''
    fdisk(p[2])
    p[0] = ('fdisk', p[2])   
def p_mount(p):
    '''
    mount : MOUNT params
    '''
    mount(p[2], mounted_partitions)
    print(mounted_partitions)
    p[0] = ('mount', p[2])

def p_unmount(p):
    '''
    unmount : UNMOUNT params
    '''
    unmount(p[2], mounted_partitions)
    p[0] = ('unmount', p[2])
def p_mkfs(p):
    '''
    mkfs : MKFS params
    '''
    mkfs(p[2], mounted_partitions, users)
    p[0] = ('mkfs', p[2])
def p_login(p):
    '''
    login : LOGIN params
    '''
    global users
    global current_partition
    users, current_partition = login(p[2], mounted_partitions)
    p[0] = ('login', p[2])
    ver_bitmaps('login'+str(p[2]),mounted_partitions, current_partition)
    add_to_journal(mounted_partitions,current_partition, str(('login', p[2])))
def p_logout(p):
    '''
    logout : LOGOUT
    '''
    global users
    exited_user = {}
    printt(f'🚶<<RUNNING LOGOUT')
    if users is not None:
        printt(f'🚶✅✅')
        exited_user = users
        users = None
    else:
        printt("🚶No user is logged in")
    add_to_journal(mounted_partitions,current_partition, str(('logout', {})))
    p[0] = ('logout', (exited_user))
def p_mkusr(p):
    '''
    mkusr : MKUSR params
    '''
    if users != None and users['username']=='root' :
        makeuser(p[2], mounted_partitions, current_partition)
        ver_bitmaps('mkusr'+str(p[2]),mounted_partitions, current_partition)
        add_to_journal(mounted_partitions,current_partition, str(('mkusr', p[2])))
    else:
        printt("🚷🚷Error: You must be logged in as root to use this command")
    
    p[0] = ('mkusr', p[2])
def p_mkgrp(p):
    '''
    mkgrp : MKGRP params
    '''
    if users != None and users['username']=='root' :
        makegroup(p[2], mounted_partitions, current_partition)
        ver_bitmaps('mkgrp'+str(p[2]),mounted_partitions, current_partition)
        add_to_journal(mounted_partitions,current_partition, str(('mkgrp', p[2])))
    else:
         printt("🚷🚷Error: You must be logged in as root to use this command")
    p[0] = ('mkgrp', p[2])
def p_rmgrp(p):
    '''
    rmgrp : RMGRP params
    '''
    if users != None and users['username']=='root' :
        remgroup(p[2], mounted_partitions, current_partition)
        ver_bitmaps('rmgrp'+str(p[2]),mounted_partitions, current_partition)
        add_to_journal(mounted_partitions,current_partition, str(('rmgrp', p[2])))
    else:
        printt("🚷🚷: You must be logged in as root to use this command")
    p[0] = ('rmgrp', p[2])
def p_rmusr(p):
    '''
    rmusr : RMUSR params
    '''
    if users != None and users['username']=='root' :
        remuser(p[2], mounted_partitions, current_partition)
        ver_bitmaps('rmusr'+str(p[2]),mounted_partitions, current_partition)
        add_to_journal(mounted_partitions,current_partition, str(('rmusr', p[2])))
    else:
        printt("🚷🚷: You must be logged in as root to use this command")
    p[0] = ('rmusr', p[2])
def p_mkfile(p):
    '''
    mkfile : MKFILE params
    '''
    if users != None:
        printt('📜  mkfile'+str(p[2]))
        mkfile(p[2], mounted_partitions, current_partition, users)
        ver_bitmaps('mkfile'+str(p[2]),mounted_partitions, current_partition)
        add_to_journal(mounted_partitions,current_partition, str(('mkfile', p[2])))
    else:
        printt("🚷🚷: You must be logged in as root to use this command")
    p[0] = ('mkfile', p[2])
def p_cat(p):
    '''
    cat : CAT params
    '''
    if users != None:
        cat(p[2], mounted_partitions, current_partition, users)
    else:
        printt("🚷🚷: You must be logged in to use this command")
    p[0] = ('cat', p[2])
def p_remove(p):
    '''
    remove : REMOVE params
    '''
    if users != None:
        remove(p[2], mounted_partitions, current_partition, users)
        ver_bitmaps('remove'+str(p[2]),mounted_partitions, current_partition)
        add_to_journal(mounted_partitions,current_partition, str(('remove', p[2])))
    else:
        printt("🚷🚷: You must be logged in to use this command")
    p[0] = ('remove', p[2])
def p_rename(p):
    '''
    rename : RENAME params
    '''
    if users != None:
        rename(p[2], mounted_partitions, current_partition, users)
        ver_bitmaps('rename'+str(p[2]),mounted_partitions, current_partition)
        add_to_journal(mounted_partitions,current_partition, str(('rename', p[2])))
    else:
        printt("🚷🚷: You must be logged in to use this command")
    p[0] = ('rename', p[2])
def p_edit(p):
    '''
    edit : EDIT params
    '''
    if users != None:
        remove(p[2], mounted_partitions, current_partition, users)
        mkfile(p[2], mounted_partitions, current_partition, users)
        ver_bitmaps('edit'+str(p[2]),mounted_partitions, current_partition)
        add_to_journal(mounted_partitions,current_partition, str(('edit', p[2])))
    else:
        printt("🚷🚷: You must be logged in to use this command")
    p[0] = ('edit', p[2])
def p_copy(p):
    '''
    copy : COPY params
    '''
    if users != None:
        copy(p[2], mounted_partitions, current_partition, users)
        ver_bitmaps('copy'+str(p[2]),mounted_partitions, current_partition)
        add_to_journal(mounted_partitions,current_partition, str(('copy', p[2])))
    else:
        printt("🚷🚷: You must be logged in to use this command")
    p[0] = ('copy', p[2])
def p_move(p):
    '''
    move : MOVE params
    '''
    if users != None:
        move(p[2], mounted_partitions, current_partition, users)
        ver_bitmaps('move'+str(p[2]),mounted_partitions, current_partition)
        add_to_journal(mounted_partitions,current_partition, str(('move', p[2])))
    else:
        printt("🚷🚷: You must be logged in to use this command")
    p[0] = ('move', p[2])
def p_find(p):
    '''
    find : FIND params
    '''
    if users != None:
        find(p[2], mounted_partitions, current_partition, users)
    else:
        printt("🚷🚷: You must be logged in to use this command")
    p[0] = ('find', p[2])
def p_pause(p):
    '''
    pause : PAUSE
    '''
    print(f'\n⏸️   <<RUNNING PAUSE_ _ _ _ _ _ _ _ _ ')
    input("Press Enter to continue...")
    p[0] = ('pause', p[1])
def p_chown(p):
    '''
    chown : CHOWN params
    '''
    if users != None:
        chown(p[2], mounted_partitions, current_partition, users)
        add_to_journal(mounted_partitions,current_partition, str(('chown', p[2])))
    else:
        printt("🚷🚷: You must be logged in to use this command")
    p[0] = ('chown', p[2])
def p_chgrp(p):
    '''
    chgrp : CHGRP params
    '''
    if users != None and users['username']=='root' :
        chgrp(p[2], mounted_partitions, current_partition, users)
        ver_bitmaps('chgrp'+str(p[2]),mounted_partitions, current_partition)
        add_to_journal(mounted_partitions,current_partition, str(('chgrp', p[2])))
    else:
        printt("🚷🚷: You must be logged in as root to use this command")
    p[0] = ('chgrp', p[2])
def p_chmod(p):
    '''
    chmod : CHMOD params
    '''
    if users != None and users['username']=='root' :
        chmod(p[2], mounted_partitions, current_partition, users)
        add_to_journal(mounted_partitions,current_partition, str(('chmod', p[2])))
    else:
        printt("🚷🚷: You must be logged in to use this command")
    p[0] = ('chmod', p[2])
def p_loss(p):
    '''
    loss : LOSS params
    '''
    loss(p[2], mounted_partitions, current_partition)
    p[0] = ('loss', p[2])
def p_recovery(p):
    '''
    recovery : RECOVERY params
    '''
    recuperar(p[2], mounted_partitions, current_partition)
    p[0] = ('recovery', p[2])
def p_rep(p):
    '''
    rep : REP params
    '''
    #if users != None:
    salida = rep(p[2], mounted_partitions,mapa_de_bytes)
    #else:
        #printt("🚷🚷: You must be logged in to use this command")
    
    p[0] = ('tree', p[2])
    
def p_error(p):
    print(f'Syntax error at {p.value!r}')

# Build the parser
parser = yacc()

# Parse an expression
#ast = parser.parse(comandos)
def display_table(titulo,mounted_partitions):
    # Create a PrettyTable object
    table = PrettyTable()
    
    # Set the column headers
    table.field_names = ["ID", "Path", "Name", "Index", "Inicio", "Size"]
    
    # Add rows to the table
    for partition_dict in mounted_partitions:
        for id_key, partition_info in partition_dict.items():
            row = [
                id_key,  # This is the ID!
                partition_info['path'],
                partition_info['name'],
                partition_info['index'],
                partition_info['inicio'],
                partition_info['size']
            ]
            table.add_row(row)
    
    # Print the table
    printt_status(titulo+"\n"+str(table))





#read C:\Users\alber\OneDrive\Escritorio\cys\MIA\proyecto1\discos_test\home\mis discos\Disco4.dsk from the byte 0 an unpack it with MBR and print it

COLORS = {'Inode': 'lightblue', 'Superblock': '#E0E0E0', 'FolderBlock': '#FFCC00', 'FileBlock': 'green', 'PointerBlock': 'orange',  'Content': '#FFCC00'}
def imprimir(obj,index):
    object_type = type(obj).__name__
    if object_type == 'FileBlock':
        obj.b_content = obj.b_content.replace('\x00', '')
    if object_type == 'FolderBlock':
        for n in obj.b_content:
            n.b_name = n.b_name.replace('\x00', '')
    table = PrettyTable(['Attribute', 'Value'])
    attributes = vars(obj)
    lista = None
    for attr, value in attributes.items():
        if not isinstance(value, list):
            table.add_row([attr, value])
        else:
            lista = value
    return object_type, table, lista,index
current_id = 0

def get_next_id():
    global current_id
    current_id += 1
    return current_id
def prettytable_to_html_string(object_type, pt, lista,index, object):
    global current_id
    get_next_id()
    header_node = f'subgraph cluster_{object_type}{index} {"{"} label = "{object_type}{index}" style = filled fillcolor = "{COLORS[object_type]}"'
    nodo_tabla = f'\n{current_id} [label='
    html_string = '''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">\n'''
    html_string += "  <TR>\n"
    for field in pt._field_names:
        html_string += f"    <TD>{field}</TD>\n"
    html_string += "  </TR>\n"
    for row in pt._rows:
        html_string += "  <TR>\n"
        for cell in row:
            cell = str(cell).replace("\n", "<BR/>")
            html_string += f"    <TD>{cell}</TD>\n"
        html_string += "  </TR>\n"

    html_string += "</TABLE>> shape=box];\n"
    #if list is not none achieve this format bloques [label="{<content0> Content: users.txt | <content1> Content: empty | <content2> Content: empty | <content3> Content: empty}"];
    bloques = f'\nnode [shape=record];\nbloques{current_id} [label='
    if lista is not None:
        bloques += '"{'
        for i,n in enumerate(lista):
            bloques += f"<content{i}> {n.__str__()} | "
        bloques += '\n}"];'
    if lista is None:
        total = header_node + nodo_tabla + html_string + "}"
    else:
        total = header_node + nodo_tabla + html_string +  bloques + "}" 
    if object_type=='FolderBlock':
        total = header_node +  bloques + "}"

    return total,current_id

#0 inode, 1 folderblock, 2 fileblock, 3 pointerblock
codigo_para_graphviz = ''
def graph(file,inicio, index):
    global codigo_para_graphviz
    if inicio == -1:
        return None
    file.seek(inicio)
    if index == 0:
        object = Inode.unpack(file.read(Inode.SIZE))
    elif index == 1:
        object = FolderBlock.unpack(file.read(FolderBlock.SIZE))
    elif index == 2:
        object = FileBlock.unpack(file.read(FileBlock.SIZE))
    elif index == 3:
        object = PointerBlock.unpack(file.read(PointerBlock.SIZE))
    object_type, pt, lista,index = imprimir(object,inicio)
    total, id = prettytable_to_html_string(object_type, pt, lista,inicio, object)
    #print(f'///////////EL ID ES {id} DEL OBJETO {object_type} CON EL INDICE {inicio}*-*-*-*-*-*-*-*-*-*-*-*-*-*')
    codigo_para_graphviz += f'\n///////////EL ID ES {id} DEL OBJETO {object_type} CON EL INDICE {inicio}*-*-*-*-*-*-*-*-*-*-*-*-*-*'
    #print(total)
    codigo_para_graphviz += "\n"+total
    if object_type== 'Inode':
        for i,n in enumerate(lista):
            if object.i_type == '0':
                apuntado = graph(file,n,1)
                if apuntado is not None:
                    #print(f"bloques{id}:<content{i}> -> bloques{apuntado}")
                    codigo_para_graphviz += f"\nbloques{id}:<content{i}> -> bloques{apuntado}"
                
            else:
                apuntado =graph(file,n,2)
                if apuntado is not None:
                    #print(f"bloques{id}:<content{i}> -> {apuntado}")
                    codigo_para_graphviz += f"\nbloques{id}:<content{i}> -> {apuntado}"
    elif object_type== 'FolderBlock':
        for i,n in enumerate(lista):
            if n.b_inodo != -1:
                apuntado =graph(file,n.b_inodo,0)
                if apuntado is not None:
                    #print(f"bloques{id}:<content{i}> -> {apuntado}")
                    codigo_para_graphviz += f"\nbloques{id}:<content{i}> -> {apuntado}"
            
    
    return id


"""while True:
    print(f'current user: {users}')
    
    display_table(mounted_partitions)
    
    s = input('>> ')
    if s == 'exit':
        break
    elif s.startswith('execute'):
        nuevo = s.split('=')
        print(nuevo)
        contenido = ''
        with open(nuevo[1], 'r') as file:
            s = file.read()
            contenido = s
        result = parser.parse(contenido)
    else:
        result = parser.parse(s)
        print(result)"""


from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse,FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from connection_manager import ws_manager
from connection_manager_status import ws_manager_status
from send import send
from send_status import send_status, printt_status

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.post("/api/query")
async def api_query(request: Request):
    try:
        # Reading JSON Body of the request.
        request_data = await request.json()
        
        # Extracting text from received JSON.
        #await ws_manager.send_log_message(f"Received query: entro")
        input_text = request_data.get('input', '')
        # For demo purposes, just sending the received text back.
        contenido = input_text
        try:
            result = parser.parse(contenido)
        except Exception as e:
            # If any error occurs, responding with the error message.
            return JSONResponse(content={"error": str(e)})
        response_data = {
            "received_text": str(result)
        }
        
        display_table(f'current user: {users}',mounted_partitions)
        send_status()   
        send()
        
        return JSONResponse(content=response_data)
    except Exception as e:
        # If any error occurs, responding with the error message.
        return JSONResponse(content={"error": str(e)})

class File(BaseModel):
    name: str
    is_png: bool
    is_svg: bool
    path: str  # Path to access the file


@app.get("/list-files", response_model=list[File])
async def list_files():
    directory = "reportes"  # Replace with the actual directory
    files_list = []
    await ws_manager.send_log_message(f"Connected to websocket")
    
    for filename in os.listdir(directory):
        if filename.endswith(".png") or filename.endswith(".jpeg") or filename.endswith(".svg"):
            is_png = filename.endswith(".png") 
            is_svg = filename.endswith(".svg")
            file_path = os.path.join(directory, filename)
            files_list.append(File(name=filename, is_png=is_png, is_svg=is_svg,path=file_path))
    
    return files_list                
                
@app.get("/get-image/{file_path:path}")
async def get_image(file_path: str):
    file_location = os.path.join(os.getcwd(), file_path)
    if os.path.exists(file_location):
        return FileResponse(file_location)
    else:
        raise HTTPException(status_code=404, detail="File not found")
import asyncio
@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()  # Accept the WebSocket connection.
    await ws_manager.connect(websocket)  # Add the WebSocket to the manager.
    try:
        while True:  # Keep the connection open and listen for messages.
            await asyncio.sleep(0.5)
            data = await websocket.receive_text()  # Receive a text message.
            print(f"Received: {data}")  # Print the received message to the console.
    except WebSocketDisconnect:  # Handle a disconnect.
        ws_manager.disconnect(websocket)  # Remove the WebSocket from the manager.



@app.websocket("/ws/status")
async def websocket_status_endpoint(websocket: WebSocket):
    await websocket.accept()  # Accept the WebSocket connection.
    await ws_manager_status.connect(websocket)  # Add the WebSocket to the manager.
    try:
        while True:  # Keep the connection open and listen for messages.
            await asyncio.sleep(0.5)
            data = await websocket.receive_text()  # Receive a text message.
            print(f"Received: {data}")  # Print the received message to the console.
    except WebSocketDisconnect:  # Handle a disconnect.
        ws_manager_status.disconnect(websocket)  # Remove the WebSocket from the manager.
