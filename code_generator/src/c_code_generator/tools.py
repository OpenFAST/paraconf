from yamale.validators import *

AUTHORIZED_CHARACTERS = ('_', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z')

FORBIDDEN_INCLUDE_NAMES = ('BOOL', 'LONG', 'DOUBLE', 'STR')



def convert_enum_to_any(enum):
    """Convert an enum to an any validator"""

    sub_types = []
    already_defined = []

    for element in enum.args:
        if isinstance(element, bool) and not 'Boolean' in already_defined:
            already_defined.append('Boolean')
            sub_types.append(Boolean())
        elif isinstance(element, int) and not 'Integer' in already_defined:
            already_defined.append('Integer')
            sub_types.append(Integer())
        elif isinstance(element, float) and not 'Number' in already_defined:
            already_defined.append('Number')
            sub_types.append(Number())
        elif isinstance(element, str) and not 'String' in already_defined:
            already_defined.append('String')
            sub_types.append(String())

    _val = Any()
    _val.validators = sub_types

    return _val


def find_nested_any(validators):
    """Find all the nested any in "validators" and return a flattened list of validators with no more any"""

    nested_count = 0
    sub_types = []

    for validator in validators:
        if isinstance(validator, Any):
            if len(validator.validators)==0:
                return []
            sub_types.extend([k for k in validator.validators if not k in sub_types])
            nested_count += 1
        elif not validator in sub_types:
            sub_types.append(validator)

    if nested_count:
        sub_types = find_nested_any(sub_types)

    return sub_types


def format_string(indices):
    """Generate a format string using indices"""

    format_string = ''
    for i in indices:
        format_string += ', %s' % (i)
    return format_string


def make_flat_tree(path_list):

    # We make a flat tree (dict) where:
    #     * the keys correspond to the current node's children dependencies
    #     * the value associated to a child dependency is a list of relative paths to its own dependencies:
    #                  / child_dependency_1: [paths to sub-dependencies_1]
    #  .{current_node} - child_dependency_2: [paths to sub-dependencies_2]
    #                  \ child_dependency_n: [paths to sub-dependencies_n]

    # If path_list is empty the current node has no children and we return None
    if path_list is None:
        return None

    struct_nodes = {}

    for path in path_list:
        # The 1st element of the splitted path is one of the current node's direct dependency
        splitted_path = path.split('.')

        # If the node has no dependency it is a primitive type
        if len(splitted_path)==1:
            struct_nodes[splitted_path[0]] = None

        # If the node has some dependencies it will be a nested struct
        else:
            # If the dependency list has not been initialized yet
            if not splitted_path[0] in struct_nodes.keys():
                struct_nodes[splitted_path[0]] = ['.'.join(splitted_path[1:])]
            # If the dependency list has already been initialized
            else:
                struct_nodes[splitted_path[0]].append('.'.join(splitted_path[1:]))

    return struct_nodes


def make_union_names(validators, path=''):
    """Generate enum names corresponding to the validators and the path to the node"""

    enum_names = []

    any_counter = 0
    list_counter = 0
    map_counter = 0

    validators_to_remove = []

    if not path=='':
        path = replace_chars(path).upper() + '_'

    for i, validator in enumerate(validators):
        
        if isinstance(validator, Any):
            enum_names.append(path+'ANY{}'.format(any_counter))
            any_counter += 1
        elif isinstance(validator, Boolean):
            if not path+'INT' in enum_names:
                enum_names.append(path+'INT')
            else:
                validators_to_remove.append(i)
        elif isinstance(validator, Integer):
            if not path+'LONG' in enum_names:
                enum_names.append(path+'LONG')
            else:
                validators_to_remove.append(i)
        elif isinstance(validator, List):
            enum_names.append(path+'LIST{}'.format(list_counter))
            list_counter += 1
        elif isinstance(validator, Map):
            enum_names.append(path+'MAP{}'.format(map_counter))
            map_counter += 1
        elif isinstance(validator, Number):
            if not path+'DOUBLE' in enum_names:
                enum_names.append(path+'DOUBLE')
            else:
                validators_to_remove.append(i)
        elif isinstance(validator, String):
            if not path+'STR' in enum_names:
                enum_names.append(path+'STR')
        elif isinstance(validator, Include):
            if validator.args[0].upper() in FORBIDDEN_INCLUDE_NAMES:
                raise ValueError('Included node ' + validator.args[0] + ' has an invalid name')
            elif not path+validator.args[0].upper() in enum_names:
                enum_names.append(path+validator.args[0].upper())
            else:
                validators_to_remove.append(i)
        else:
            print(validator)

    for i in validators_to_remove:
        validators.pop(i)
    
    enum_string = 'enum {'
    for name in enum_names[:-1]:
        enum_string += name + ', '
    enum_string += enum_names[-1] + '}'

    return enum_names, enum_string


def replace_chars(string):
    """Modify the string to replace all forbidden characters"""

    new_string = ''
    if string[0] in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'):
        # A variable cannot begin by a number in C
        new_string += '_'
    for i in range(len(string)):
        if string[i] not in AUTHORIZED_CHARACTERS:
            new_string += '_'
        else:
            new_string += string[i]
    return new_string
