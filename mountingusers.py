def load_users_from_content(content):
    """Load users and groups from a string content into a dictionary structure."""
    lines = content.split("\n")
    

    data_structure = {}
    for line in lines:
        if line == '':
            continue
        parts = line.strip().split(",")
        if parts[1] == 'G':  # Group
            if parts[0] != '0':
                data_structure[parts[2]] = {}
        else:  # User
            if parts[0] != '0':
                group_name = parts[2]
                user_data = {
                    'id': parts[0],
                    'username': parts[3],
                    'password': parts[4]
                }
                if group_name in data_structure:
                    data_structure[group_name][parts[3]] = user_data
                else:
                    data_structure[group_name] = {parts[3]: user_data}

    return data_structure
def parse_users(texto):
    lines = texto.split('\n')
    #print("ESTAS SON LAS LINEAS EN EL PARSE USERS")
    #print(lines)
    users_list = []
    
    # Temporary storage for groups
    groups = {}
    grupo_actual = ''
    for line in lines:
        parts = line.split(',')
        
        # Group
        if len(parts) == 3 and parts[1] == 'G'and parts[0]!='0':
            groups[parts[2]] = parts[0]
            grupo_actual = parts[2]
        
        # User
        elif len(parts) == 5 and parts[1] == 'U' and parts[0]!='0':
            if grupo_actual == parts[2]:
                user_data = {
                    parts[3]: {
                        'id': parts[0],
                        'username': parts[3],
                        'password': parts[4],
                        'group': parts[2]
                    }
                }
                users_list.append(user_data)
            
    return users_list


def get_user_if_authenticated(usuarios, user, password):
    #print(f'buscando a {user} con password {password} en {usuarios}')
    for user_data in usuarios:
        if user in user_data:
            # User found
            if user_data[user]['password'] == password:
                # Password matches
                return user_data[user]
    # User not found or password doesn't match
    return None

def get_id_by_group(grupos, group):
    for item in grupos:
        user_data = item[next(iter(item))]
        if user_data['group'] == group:
            return user_data['id']
    return None  # If the group was not found


def extract_active_groups(text):
    lines = text.split("\n")
    groups = []
    #print(lines)
    for line in lines:
        if line == '':
            continue
        parts = line.split(",")
        # Check if the record is for a group and is active
        if parts[1] == 'G' and parts[0] != '0':
            groups.append({'groupname': parts[2], 'id': int(parts[0])})

    return groups
def get_group_id(group_name, groups):
    for group in groups:
        if group['groupname'] == group_name:
            return group['id']
    return None
