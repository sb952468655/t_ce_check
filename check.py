import re, os
import difflib

def ssh(config):
    '''ssh下一行要检测到server-shutdown'''

    err = ''
    p_ssh = r'(?s)ssh\n.*?\n {12}exit'
    res_ssh = re.search(p_ssh, config)

    if res_ssh:
        ssh_lines = res_ssh.group().splitlines()
        if ssh_lines[1] != '                server-shutdown':
            err = 'ssh下一行没有检测到server-shutdown'

            #在log中标记错误
            flag_str = ssh_lines[0] + '\n +                server-shutdown\n' + '\n'.join(ssh_lines[1:])
            config = config.replace(res_ssh.group(), flag_str)
    else:
        err = '没有找到ssh配置，请检查'

    if err == '':
        err = '检查通过'

    return err


def ftp(config):
    '''System Security Configuration下5行内，检测不到ftp'''

    err = ''
    p_system_security_configuration = '(?s)echo "System Security Configuration"\n#-{50}\n.*?\n#-{50}'

    res_system_security_configuration = re.search(p_system_security_configuration, config)
    if res_system_security_configuration:
        str_lines = res_system_security_configuration.group().splitlines()
        for i in str_lines[:6]:
            if 'ftp-server' in i:
                err = 'System Security Configuration 中存在 ftp'

                #在log中标记错误
                new_str = res_system_security_configuration.group().replace(i, ' -' + i)
                config = config.replace(res_system_security_configuration.group(), new_str)
    else:
        err = '没有找到 System Security Configuration 请检查'

    if err == '':
        err = '检查通过'
    return err


def qos(config1):
    '''echo "QoS Policy Configuration"，对比JS-NJ-GL-CE-3.CDMA（115.168.128.180）'''

    err = ''
    g_config_ce = open('JS-NJ-GL-CE-3.CDMA.log').read()
    p_qos = r'''(?s)(qos\n.*?\n {4}exit)'''

    res_qos = re.findall(p_qos, config1)
    res_ce_qos = re.findall(p_qos, g_config_ce)

    if not res_qos:
        err = '配置1中没有找到 QoS Policy Configuration 请检查'
        return err

    host_1_name = get_host_name(config1)

    file_path = os.path.join('检查结果', '{}'.format(host_1_name))
    if not os.path.exists(file_path):
        os.makedirs(file_path)

    if res_qos[0] != res_ce_qos[0]:
        res_str = remove_right_space(res_qos[0])
        model_str = remove_right_space(res_ce_qos[0])
        if res_str != model_str:
            err += diff(res_str, model_str) + '\n'

    if res_qos[1] != res_ce_qos[1]:
        
        res_str = remove_right_space(res_qos[1])
        model_str = remove_right_space(res_ce_qos[1])
        if res_str != model_str:
            err += diff(res_str, model_str) + '\n'

    if err == '':
        err = '检查通过'

    return err

def isis_bfd(config):
    '''echo "ISIS Configuration"，每个interface下（interface "system"忽略）有bfd-enable ipv4的配置'''

    err = ''
    p_isis = r'(?s)(        isis.*?\n {8}exit)'

    p_interface = r'(?s)(interface "(.*?)".*?\n {12}exit)'

    res_isis = re.search(p_isis, config)

    if not res_isis:
        err = '没有找到ISIS Configuration，请检查'
        return err

    res_interface = re.findall(p_interface, res_isis.group())
    if res_interface == []:
        err = 'ISIS Configuration 中没有找到 interface，请检查'
        return err

    for item in res_interface:
        if item[1] == 'system':
            continue

        if 'bfd-enable ipv4' not in item[0]:
            err += 'ISIS Configuration interface "{}" 中没有 bfd-enable ipv4\n'.format(item[1])

            #标记错误
            str_lines = item[0].splitlines()
            new_str = '{}\n +                bfd-enable ipv4\n{}'.format('\n'.join(str_lines[:3]), '\n'.join(str_lines[3:]))
            config = config.replace(item[0], new_str)

    if err == '':
        err = '检查通过'
    return err

def static_route_bfd(config):
    '''echo "Static Route Configuration" 和 vprn 中，每个static-route-entry下有bfd-enable'''

    err = ''
    p_static_route_configuration = r'''(?s)(echo "Static Route Configuration"\n#-{50}.*?\n#-{50})'''
    p_vprn = r'(?s)(vprn (\d{3,7}) .*?\n {8}exit)'
    p_vprn_static_route = r'(?s)(            (static-route-entry \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}|[a-z0-9]{1,4}:[a-z0-9]{1,4}:[a-z0-9]{1,4}::[a-z0-9]{0,4}/\d{1,2})\n.*?\n {12}exit)'

    res_static_route_configuration = re.search(p_static_route_configuration, config)
    if not res_static_route_configuration:
        err = '没有找到Static Route Configuration，请检查\n'
        return err

    p_static_route_entry = r'(?s)(            (static-route-entry \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}|[a-z0-9]{1,4}:[a-z0-9]{1,4}:[a-z0-9]{1,4}::[a-z0-9]{0,4}/\d{1,2}).*?\n {8}exit)'
    res_static_route_entry = re.findall(p_static_route_entry, res_static_route_configuration.group())

    for item in res_static_route_entry:
        if 'bfd-enable' not in item[0] and 'black-hole' not in item[0]:
            # err += 'Static Route Configuration {} 中没有找到bfd-enable，请检查\n'.format(item[1])

            #在log中标记错误
            str_lines = item[0].splitlines()
            err += "{}\n{}\n{}\n{}\n".format(str_lines[0], str_lines[1], ' +                bfd-enable', '\n'.join(str_lines[2:]))
            # config = config.replace(item[0], new_str)


    res_vprn = re.findall(p_vprn, config)
    for vprn in res_vprn:
        res_vprn_static_route = re.findall(p_vprn_static_route, vprn[0])
        for vprn_static_route in res_vprn_static_route:
            if 'bfd-enable' not in vprn_static_route[0] and 'black-hole' not in vprn_static_route[0]:
                # err += 'vprn {} {} 中没有找到bfd-enable，请检查\n'.format(vprn[1], vprn_static_route[1])

                #标记错误
                str_lines = vprn_static_route[0].splitlines()
                err += "{}\n{}\n{}\n{}\n".format(str_lines[0], str_lines[1], ' +                    bfd-enable', '\n'.join(str_lines[2:]))
                # config = config.replace(vprn_static_route[0], new_str)

    if err == '':
        err = '检查通过'
    return err


def bgp_bfd(config):
    '''bgp下面5行内匹配到group的，都要在15行内匹配到bfd-enable'''

    err = ''
    p_bgp = r'(?s)(bgp.*?\n {8}exit)'
    p_gruop = r'(?s)(                (group ".*?").*?\n {16}exit)'

    res_bgp = re.search(p_bgp, config)

    if not res_bgp:
        err = '没有找到 BGP Configuration，请检查'
        return err

    res_group = re.findall(p_gruop, res_bgp.group())

    if res_group == []:
        err = 'BGP Configuration 中没有找到 group 请检查'
        return err

    for item in res_group:
        if 'bfd-enable' not in item[0]:

            #标记错误
            str_lines = item[0].splitlines()
            new_str = ''
            for i in str_lines:
                if 'peer-as' in i:
                    err += i + '\n +                  bfd-enable\n'
                else:
                    err += i + '\n'

            config = config.replace(item[0], new_str)

    if err == '':
        err = '检查通过'
    return err

def policy_options(config, config2):
    '''policy-options下prefix-list地址，一对CE要求地址完全一致
    prefix-list中匹配有exact的地址段，都要对应的有static-route-entry'''

    err = ''
    p_policy_options = r'(?s)(policy-options.*?\n {8}exit)'
    res_policy_options = re.search(p_policy_options, config)
    res_policy_options2 = re.search(p_policy_options, config2)

    host_1_name = get_host_name(config)
    host_2_name = get_host_name(config2)

    if not res_policy_options:
        err = '{} 中没有找到policy-options，请检查'.format(host_1_name)
        return err

    if not res_policy_options2:
        err = '{} 中没有找到policy-options，请检查'.format(host_2_name)
        return err

    p_prefix_list = r'(?s)((prefix-list ".*?")\n {16}prefix.*?\n {12}exit)'

    res_prefix_list = re.findall(p_prefix_list, res_policy_options.group())
    res_prefix_list2 = re.findall(p_prefix_list, res_policy_options2.group())

    if res_prefix_list == []:
        err = '{} policy-options 中没有找到 prefix-list，请检查\n'.format(host_1_name)
        return err

    if res_prefix_list2 == []:
        err = '{} policy-options 中没有找到 prefix-list，请检查\n'.format(host_2_name)
        return err


    p_address = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}|[a-z0-9]{1,4}:[a-z0-9]{1,4}:[a-z0-9]{1,4}::[a-z0-9]{0,4}/\d{1,2})'
    for item in res_prefix_list:
        res_address = re.findall(p_address, item[0])
        if res_address == []:
            err += '{} policy-options {} 中没有发现地址，请检查'.format(host_1_name, item[1])
            continue


        #检查 config2 prefix-list 中的地址是否一致
        for item2 in res_prefix_list2:
            if item2[1] == item[1]:
                res_address2 = re.findall(p_address, item2[0])
                if res_address2 == []:
                    err = 'config2 policy-options {} 中没有发现地址，请检查\n'.format(item2[1])
                    return err

                if sorted(res_address) != sorted(res_address2):

                    address_1_more = []
                    address_2_more = []

                    for item3 in res_address:
                        if item3 not in res_address2:
                            address_1_more.append(item3)

                    for item3 in res_address2:
                        if item3 not in res_address:
                            address_2_more.append(item3)

                    err += '{}和{} 中的 {} 地址不一致，请检查\n\n'.format(host_1_name, host_2_name, item[1])
                    new_prelist = item[0]
                    new_prelist2 = item2[0]
                    if address_1_more:
                        err += '{}比{} 多出的address\n\n{}\n\n'.format(host_1_name, host_2_name, '\n'.join(address_1_more))

                        #标记地址
                        for i in new_prelist.splitlines():
                            for j in address_1_more:
                                if j in i:
                                    new_prelist = new_prelist.replace(i, ' c-d' + i)

                        temp = ''
                        for i in address_1_more:
                            temp += ' c-d                prefix {}  exact\n'.format(i)
                        temp += '            exit'
                        
                        new_prelist2 = new_prelist2.replace('            exit', temp)


                    if address_2_more:
                        err += '{}比{} 多出的address\n\n{}\n\n'.format(host_2_name, host_1_name, '\n'.join(address_2_more))

                        #标记地址
                        for i in new_prelist2.splitlines():
                            for j in address_2_more:
                                if j in i:
                                    new_prelist2 = new_prelist2.replace(i, ' c-d' + i)

                        temp = ''
                        for i in address_2_more:
                            temp += ' c-d                prefix {}  exact\n'.format(i)
                        temp += '            exit'
                        
                        new_prelist = new_prelist.replace('            exit', temp)

                    
                    config = config.replace(item[0], new_prelist)
                    config2 = config2.replace(item2[0], new_prelist2)

                break

    #两个检查之间区分
    err += '\n\n'
    
    res_policy_options = re.search(p_policy_options, config)
    res_policy_options2 = re.search(p_policy_options, config2)
    res_prefix_list = re.findall(p_prefix_list, res_policy_options.group())
    res_prefix_list2 = re.findall(p_prefix_list, res_policy_options2.group())
    #找到有exact的address
    p_exact_address = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}|[a-z0-9]{1,4}:[a-z0-9]{1,4}:[a-z0-9]{1,4}::[a-z0-9]{0,4}/\d{1,3}) exact'
    for item in res_prefix_list:
        if item[1].endswith('-IN"') or item[1].endswith('-in"'):
            continue
        res_exact_address = re.findall(p_exact_address, item[0])
        new_prefix_str = item[0]
        for item2 in res_exact_address:
            if 'static-route-entry {}'.format(item2) not in config:
                err += '{} {} 中的 {} 没有对应 static-route-entry，请检查\n'.format(host_1_name, item[1], item2)

                #标记错误
                new_prefix_str = new_prefix_str.replace('                prefix {} exact'.format(item2), ' q-s                prefix {} exact'.format(item2))

        config = config.replace(item[0], new_prefix_str)

    for item in res_prefix_list2:
        if item[1].endswith('-IN"') or item[1].endswith('-in"'):
            continue
        res_exact_address = re.findall(p_exact_address, item[0])
        new_prefix_str = item[0]
        for item2 in res_exact_address:
            if 'static-route-entry {}'.format(item2) not in config2:
                err += '{} {} 中的 {} 没有对应 static-route-entry，请检查\n'.format(host_2_name, item[1], item2)

                #标记错误
                new_prefix_str = new_prefix_str.replace('                prefix {} exact'.format(item2), ' q-s                prefix {} exact'.format(item2))

        config2 = config2.replace(item[0], new_prefix_str)

    if err == '':
        err = '检查通过'
    return err, config, config2

def ip_filter_200(config1):
    '''对比JS-NJ-GL-CE-3.CDMA（115.168.128.180），要求ip-filter 200完全一致
    interface下一行description中含有163的，在10行内要有filter ip 200'''

    err = ''
    config_ce = open('JS-NJ-GL-CE-3.CDMA.log').read()
    p_filter_ip_200 = r'(?s)(ip-filter 200 create.*?\n {8}exit)'
    res_filter_ip_200_1 = re.search(p_filter_ip_200, config1)
    res_filter_ip_200_ce = re.search(p_filter_ip_200, config_ce)

    host_1_name = get_host_name(config1)

    if not res_filter_ip_200_1:
        err = '{}没有找到ip-filter 200，请检查\n'.format(host_1_name)
        return err

    if not res_filter_ip_200_ce:
        err += 'JS-NJ-GL-CE-3.CDMA 中没有找到ip-filter 200，请检查\n'
        return err

    if res_filter_ip_200_1.group() != res_filter_ip_200_ce.group():
        res_str = remove_right_space(res_filter_ip_200_1.group())
        model_str = remove_right_space(res_filter_ip_200_ce.group())
        if res_str != model_str:
            err += diff(res_str, model_str) + '\n'


    p_interface = r'(?s)(interface "(.*?)".*?\n {12}exit)'

    res_interface = re.findall(p_interface, config1)

    if res_interface == []:
        err += '{}没有找到interface，请检查\n'.format(host_1_name)
        return err

    for item in res_interface:
        p_description = r'description ".*?"'

        res_description = re.search(p_description, item[0])
        if res_description and '163' in res_description.group():
            enter_index = 0
            for i in range(11):
                index = item[0].find('\n', enter_index + 1)

                if index == -1:
                    break
                else:
                    enter_index = index

            if item[0].find('filter ip 200', 0, enter_index) == -1:
                err += '{} interface "{}" 没有filter ip 200 请检查\n'.format(host_1_name ,item[1])

                #标记错误
                str_lines = item[0].splitlines()
                new_str = ''
                for i in str_lines:
                    if i.startswith('                sap'):
                        filter_ip = '\n +                    ingress\n +                        filter ip 200\n +                    exit\n'
                        new_str += i + filter_ip
                    else:
                        new_str += i + '\n'

                # config1 = config1.replace(item[0], new_str)

    if err == '':
        err = '检查通过'
    return err

def prefix_static_route_check(config):
    '''检查prefix-list地址段中是否配置了黑洞路由'''

    err = ''
    p_prefix_list = r'(?s)(prefix-list "(.{5,30}-IN)"\n.*?\n {12}exit)'
    p_prefix = r'prefix (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\w\w) '

    res_prefix_list = re.findall(p_prefix_list, config)

    for item in res_prefix_list:
        res_prefix = re.findall(p_prefix, item[0])
        for item_2 in res_prefix:
            p_static_route = r'(?s)(static-route-entry {}.*?\n {12}exit)'.replace('{}', item_2)
            res_static_route = re.search(p_static_route, config)
            if res_static_route:
                res_static_route.group()
            if res_static_route and ' black-hole' in res_static_route.group():
                err += 'prefix-list "{}" 中 {} 配置了黑洞路由，请维护人员进行确认配置是否正确\n'.format(item[1], item_2)

    
    return err

def vprn_static_route_check(config):
    '''检查垃圾静态路由模块'''

    err = ''
    p_vprn = r'(?s)(vprn (\d{3,7}) .*?\n {8}exit)'
    p_static_route = r'(?s)(static-route-entry (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\w\w|[a-z0-9]{1,4}:[a-z0-9]{1,4}:[a-z0-9]{1,4}::[a-z0-9]{0,4}/\d{1,3}).*?\n {12}exit)'
    p_static_route2 = r'(static-route (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\w\w|[a-z0-9]{1,4}:[a-z0-9]{1,4}:[a-z0-9]{1,4}::[a-z0-9]{0,4}/\d{1,3}) next-hop \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    p_next_hop = r'next-hop (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'

    res_vprn = re.findall(p_vprn, config)
    address = []
    for vprn in res_vprn:
        res_static_route = re.findall(p_static_route, vprn[0])
        res_static_route2 = re.findall(p_static_route2, vprn[0])
        if not res_static_route:
            res_static_route = res_static_route2
        for static_route in res_static_route:
            if 'next-hop' in static_route[0] and 'black-hole' not in static_route[0]:
                res_next_hop = re.search(p_next_hop, static_route[0])
                if res_next_hop and res_next_hop.group(1) not in address:
                    address.append(res_next_hop.group(1))
                    err += 'ping router {} {}\nshow router {} route-table {}\n'.format(vprn[1], res_next_hop.group(1)
                    , vprn[1], res_next_hop.group(1))
    return err

def policy_options_diff(config, config2):
    '''路由发布对比'''

    err = ''
    config3 = config
    config4 = config2
    p_policy_options = r'(?s)(policy-options.*?\n {8}exit)'
    res_policy_options_config_1 = re.search(p_policy_options, config)
    res_policy_options_config_2 = re.search(p_policy_options, config2)

    host_1_name = get_host_name(config)
    host_2_name = get_host_name(config2)

    if not res_policy_options_config_1:
        err = '{}没有找到policy-options，请检查'.format(host_1_name)
        return err

    if not res_policy_options_config_2:
        err = '{}没有找到policy-options，请检查'.format(host_2_name)
        return err

    res_str_1 = remove_right_space(res_policy_options_config_1.group())
    res_str_2 = remove_right_space(res_policy_options_config_2.group())
    if res_str_1 != res_str_2:
        diff1 = diff(res_str_1, res_str_2) + '\n'
        err += diff1
        diff2 = diff(res_str_2, res_str_1) + '\n'
        err += diff2
        config3 = config3.replace(res_policy_options_config_1.group(), diff1)
        config4 = config4.replace(res_policy_options_config_2.group(), diff2)
        config3 = add_flag(config3)
        config4 = add_flag(config4)

    if err == '':
        err = '检查通过'

    return err,config3, config4

def cpm_filter_check(config1, config2):
    '''System Security Cpm下，一对CE配置要求一致（system地址除外）'''
    
    err = ''
    p_cpm_filter = r'(?s)(echo "System Security Cpm Hw Filters, PKI, TLS and LDAP Configuration"\n.*?\n {4}exit)'
    p_system_address = r'(?s)(interface "system"\n {12}address (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\w\w))'

    res_config_1_cpm_filter = re.search(p_cpm_filter, config1)
    res_config_2_cpm_filter = re.search(p_cpm_filter, config2)
    res_config_1_system_address = re.search(p_system_address, config1)
    res_config_2_system_address = re.search(p_system_address, config2)

    host_1_name = get_host_name(config1)
    host_2_name = get_host_name(config2)

    if not res_config_1_cpm_filter:
        err = '{}中没有找到System Security Cpm Hw Filters, PKI, TLS and LDAP Configuration请检查'.format(host_1_name)
        return err

    if not res_config_2_cpm_filter:
        err = '{}中没有找到System Security Cpm Hw Filters, PKI, TLS and LDAP Configuration请检查'.format(host_2_name)
        return err

    if not res_config_1_system_address:
        err = '{}中没有找到System 地址请检查'.format(host_2_name)
        return err

    if not res_config_2_system_address:
        err = '{}中没有找到System 地址请检查'.format(host_2_name)
        return err
    

    # config_1_cpm_filter = res_config_1_cpm_filter.group().replace(res_config_1_system_address.group(2), res_config_1_system_address.group(2) + ' #python标注system地址')
    # config_2_cpm_filter = res_config_2_cpm_filter.group().replace(res_config_2_system_address.group(2), res_config_2_system_address.group(2) + ' #python标注system地址')
    config_1_cpm_filter = res_config_1_cpm_filter.group()
    config_2_cpm_filter = res_config_2_cpm_filter.group()

    if config_1_cpm_filter != config_2_cpm_filter:

        html_path = os.path.join('检查结果', '{}与JS-NJ-GL-CE-3.CDMA及{} 对比检查结果.log'.format(host_1_name, host_2_name))
        err += '{}与{} cpm-filter 对比不一致，请打开 {} 查看\n'.format(host_1_name, host_2_name, os.path.join(os.getcwd(),html_path))

    if err == '':
        err = '检查通过'

    return err, config_1_cpm_filter, config_2_cpm_filter
    
def check_static_router(config):
    '''静态路由错误配置检查'''

    err = ''
    err_static_route = []
    host_1_name = get_host_name(config)
    p_static_route_configuration = r'(?s)(echo "Static Route Configuration"\n#-{50}.*?\n#-{50})'
    p_static_route = r'( {8}static-route \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}( next-hop)? "black-hole" preference \d{1,3})'

    res_static_route_configuration = re.search(p_static_route_configuration, config)

    if res_static_route_configuration:
        res = re.findall(p_static_route, res_static_route_configuration.group())
        res_static_route = re.findall(p_static_route, config)

        if res:
            for i in res:
                if 'next-hop' in i:
                    err_static_route.append(i[0])
                    err += '{} 中的 {} 配置错误\n'.format(host_1_name, i[0])

        for i in res_static_route:
            if ' next-hop' == i[2]:
                err_static_route.append(i[0])
                err += '{} 中的 {} 配置错误\n'.format(host_1_name, i[1].strip())
            elif 'next-hop "black-hole"' in i[0]:
                err_static_route.append(i[0])
                err += '{} 中的 {} 配置错误\n'.format(host_1_name, i[1].strip())

    if err == '':
        err = '检查通过'
    
    return err

def check_user(config):
    '''配置必须有 no user "admin"'''

    host_1_name = get_host_name(config)
    if 'no user "admin"' in config:
        return '检查通过'
    else:
        return '{} 中没有 no user "admin" 配置，请检查'.format(host_1_name)

def static_config_check(config):
    '''CE配置静态检查”模块：将原程序1、2、3、4、5、6、7、8、10、11、13项合为“CE配置静态检查”项'''

    err_text = ''

    host_name = get_host_name(config)
    err_text = '1、user\n\n'+ host_name + '\n\n' + check_user(config) + '\n\n'

    err = ssh(config)
    err_text += '2、ssh\n\n' + host_name + '\n\n' + err + '\n\n'

    err = ftp(config)
    err_text += '3、ftp\n\n' + host_name + '\n\n' + err + '\n\n'

    err = qos(config)
    err_text += '4、qos\n\n' + err + '\n\n'

    err = isis_bfd(config)
    err_text += '5、isis bfd\n\n' + host_name + '\n\n' + err + '\n\n'

    err = static_route_bfd(config)
    err_text += '6、static-route bfd\n\n' + host_name + '\n\n' + err + '\n\n'

    err = bgp_bfd(config)
    err_text += '7、bgp bfd\n\n' + host_name + '\n\n' + err + '\n\n'

    err = ip_filter_200(config)
    err_text += '8、ip-filter 200限制\n\n' + err + '\n\n'

    err = check_static_router(config)
    err_text += '9、静态路由错误配置检查\n\n' + err + '\n\n'

    return err_text

def static_route_check(config):
    '''CE垃圾静态路由检查”模块菜单下包含：
    1、生成CE检查脚本（可以导出，供用户在设备上使用）；
    2、导入CE检查log（用户使用上步骤的脚本在设备上执行产生的log）；
    3、检查，输出检查结果；4、导出检查结果'''

    err = ''

    return err

def double_ce_route_check(config):
    '''成对CE路由发布对比
    -？ 表示自己比对方CE多的路由发布条目
    +？ 表示自己比对方CE少的路由发布条目'''



# def all_check(config, config2):
#     '''检查所有项'''

#     config3 = ''
#     config4 = ''
#     err_text = ''
#     host_1_name = get_host_name(config)
#     host_2_name = get_host_name(config2)

#     err_text = '1、user\n\n'+ host_1_name + '\n\n' + check_user(config) + '\n\n'
#     err_text += host_2_name + '\n\n' + check_user(config2) + '\n\n\n\n\n\n'

#     err, config3 = ssh(config)
#     err_text += '2、ssh\n\n' + host_1_name + '\n\n' + err + '\n\n'
#     err, config4 = ssh(config2)
#     err_text += host_2_name + '\n\n' + err + '\n\n\n\n\n\n'

#     err, config3 = ftp(config3)
#     err_text += '2、ftp\n\n' + host_1_name + '\n\n' + err + '\n\n'
#     err, config4 = ftp(config4)
#     err_text += host_2_name + '\n\n' + err + '\n\n\n\n\n\n'

#     err, config3, config4 = qos(config3, config4)
#     err_text += '4、qos\n\n' + err + '\n\n\n\n\n\n'

#     err, config3 = isis_bfd(config3)
#     err_text += '5、isis bfd\n\n' + host_1_name + '\n\n' + err + '\n\n'
#     err, config4 = isis_bfd(config4)
#     err_text += host_2_name + '\n\n' + err + '\n\n\n\n\n\n'

#     err, config3 = static_route_bfd(config3)
#     err_text += '6、static-route bfd\n\n' + host_1_name + '\n\n' + err + '\n\n'
#     err, config4 = static_route_bfd(config4)
#     err_text += host_2_name + '\n\n' + err + '\n\n\n\n\n\n'

#     err, config3 = bgp_bfd(config3)
#     err_text += '7、bgp bfd\n\n' + host_1_name + '\n\n' + err + '\n\n'
#     err, config4 = bgp_bfd(config4)
#     err_text += host_2_name + '\n\n' + err + '\n\n\n\n\n\n'

#     err, config3, config4 = policy_options(config3, config4)
#     err_text += '8、policy-options\n\n' + err + '\n\n\n\n\n\n'
#     policy_options_err, policy_options_config_1, policy_options_config_2 = policy_options_diff(config, config2)

#     err_text += '9、路由发布对比\n\n' + policy_options_err + '\n\n\n\n\n\n'
#     cpm_filter_err, config_1_cpm_filter, config_2_cpm_filter = cpm_filter_check(config, config2)

#     err_text += '10、cpm-filter\n\n' + cpm_filter_err + '\n\n\n\n\n\n'
#     err, config3, config4 = ip_filter_200(config3, config4)

#     err_text += '11、ip-filter 200限制\n\n' +  err + '\n\n\n\n\n\n'

#     err_text += '12、垃圾静态路由检查\n\n' + host_1_name + ' 检查命令脚本\n\n' + vprn_static_route_check(config) + '\n' \
#         + host_2_name + ' 检查命令脚本\n\n' + vprn_static_route_check(config2) + '\n\n\n\n\n\n'

#     err, err_static_route, err_static_route_2 = check_static_router(config, config2)
#     err_text += '13、静态路由错误配置检查\n\n' + err + '\n\n\n\n\n\n'

#     if policy_options_err != '检查通过':
#         text1_lines = policy_options_config_1.splitlines()
#         text2_lines = policy_options_config_2.splitlines()
#         d = difflib.Differ()

#         if config3:
#             diff = d.compare(text1_lines, text2_lines)
#             diff_str = "\n".join(list(diff))
#             config3 = config3.replace(policy_options_config_1, diff_str)

#         if config4:
#             diff = d.compare(text2_lines, text1_lines)
#             diff_str = "\n".join(list(diff))
#             config4 = config4.replace(policy_options_config_2, diff_str)


#     if cpm_filter_err != '检查通过':
#         text1_lines = config_1_cpm_filter.splitlines()
#         text2_lines = config_2_cpm_filter.splitlines()
#         d = difflib.Differ()

#         if config3:
#             diff = d.compare(text1_lines, text2_lines)
#             diff_str = "\n".join(list(diff))
#             config3 = config3.replace(config_1_cpm_filter, diff_str)

#         if config4:
#             diff = d.compare(text2_lines, text1_lines)
#             diff_str = "\n".join(list(diff))
#             config4 = config4.replace(config_2_cpm_filter, diff_str)

#     if err != '检查通过':
#         for i in err_static_route:
#             temp = ''
#             for j in i.splitlines():
#                 temp += ' x' + j + '\n'
#             config3 = config3.replace(i, temp)

#         for i in err_static_route_2:
#             temp = ''
#             for j in i.splitlines():
#                 temp += ' x' + j + '\n'
#             config4 = config4.replace(i, temp)

#     #把与ce3对比结果写入文件
#     if not os.path.exists('检查结果'):
#         os.makedirs('检查结果')
#     p_system_address = r'(?s)(interface "system"\n {12}address (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\w\w))'
#     res_system_address_1 = re.search(p_system_address, config3)
#     res_system_address_2 = re.search(p_system_address, config4)
#     if config3:
#         if res_system_address_1 and res_system_address_2:
#             config3 = config3.replace(res_system_address_1.group(2), res_system_address_1.group(2) + ' #python标注system地址')
#             config3 = config3.replace(res_system_address_2.group(2), res_system_address_2.group(2) + ' #python标注system地址')
#         log_path = os.path.join('检查结果', '{}与JS-NJ-GL-CE-3.CDMA及{} 对比检查结果.log'.format(host_1_name, host_2_name))
#         with open(log_path, 'w', encoding='utf-8') as f:
#             f.write(config3)

#     if config4:
#         if res_system_address_1 and res_system_address_2:
#             config4 = config4.replace(res_system_address_1.group(2), res_system_address_1.group(2) + ' #python标注system地址')
#             config4 = config4.replace(res_system_address_2.group(2), res_system_address_2.group(2) + ' #python标注system地址')
#         log_path = os.path.join('检查结果', '{}与JS-NJ-GL-CE-3.CDMA及{} 对比检查结果.log'.format(host_2_name, host_1_name))
#         with open(log_path, 'w', encoding='utf-8') as f:
#             f.write(config4)

#     return err_text

def get_host_name(config):
    '''获取设备名称'''

    p_host_name = r'(?s)(system\n {8}name "(.*?)")'
    res_host_name = re.search(p_host_name, config)
    if not res_host_name:
        host_name = ''
    else:
        host_name = res_host_name.group(2)

    return host_name

def add_flag(config):
    '''在文件对比标识符： + - ? 前空格，以便区分'''

    res = config.replace('\n-', '\n -')
    res = res.replace('\n+', '\n +')
    res = res.replace('\n?', '\n ?')

    return res

def diff(text1, text2):
    '''文本对比'''

    text1_lines = text1.splitlines()
    text2_lines = text2.splitlines()

    d = difflib.Differ()
    diff = d.compare(text1_lines, text2_lines)

    return "\n".join(list(diff))

def remove_right_space(text):
    '''去掉每行右边空格'''

    res = ''
    for i in text.splitlines():
        res += i.rstrip() + '\n'

    return res.rstrip()