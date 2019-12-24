import re, os
import difflib


def ssh(config):
    '''ssh下一行要检测到server-shutdown'''

    err = ''
    p_ssh = r'''ssh\n                server-shutdown'''
    res_ssh = re.search(p_ssh, config)

    if not res_ssh:
        err = 'ssh下一行没有检测到server-shutdown'
    if err == '':
        err = '检查通过'

    return err


def ftp(config):
    '''System Security Configuration下5行内，检测不到ftp'''

    err = ''
    system_index = config.find('System Security Configuration')

    if system_index == -1:
        err = '没有找到 System Security Configuration'
        return

    enter_index = system_index
    for i in range(6):
        index = config.find('\n', enter_index + 1)
        if index == -1:
            break
        else:
            enter_index = index

    ftp_index = config.find('ftp', system_index, enter_index)
    if ftp_index != -1:
        err = 'System Security Configuration 中存在 ftp'

    if err == '':
        err = '检查通过'
    return err


def qos(config1,config2):
    '''echo "QoS Policy Configuration"，对比JS-NJ-GL-CE-3.CDMA（115.168.128.180）'''

    err = ''
    config_ce = open('JS-NJ-GL-CE-3.CDMA.log').read()
    p_qos = r'''(?s)(qos\n.*?\n {4}exit)'''

    res_qos = re.findall(p_qos, config1)
    res_qos2 = re.findall(p_qos, config2)
    res_ce_qos = re.findall(p_qos, config_ce)

    if not res_qos:
        err = '配置1中没有找到 QoS Policy Configuration 请检查'
        return err

    if not res_qos2:
        err = '配置2中没有找到 QoS Policy Configuration 请检查'
        return err

    hd = difflib.HtmlDiff()

    host_1_name = get_host_name(config1)
    host_2_name = get_host_name(config2)


    file_path = os.path.join('检查结果', '{}和{}'.format(host_1_name, host_2_name))
    if not os.path.exists(file_path):
        os.makedirs(file_path)

    if '\n'.join(res_qos) != '\n'.join(res_ce_qos):
        
        html_path = os.path.join(file_path, '{}与JS-NJ-GL-CE-3.CDMA.log qos对比检查结果.html'.format(host_1_name))
        err += '{}与JS-NJ-GL-CE-3.CDMA.log qos 对比不一致，请查看 {}\n'.format(host_1_name, os.path.join(os.getcwd(), html_path))

        with open(html_path,'w') as fo:
            fo.write(hd.make_file('\n'.join(res_qos).split('\n'), '\n'.join(res_ce_qos).split('\n')))
            fo.close()

    if '\n'.join(res_qos2) != '\n'.join(res_ce_qos):
        html_path = os.path.join(file_path, '{}与JS-NJ-GL-CE-3.CDMA.log qos对比检查结果.html'.format(host_2_name))
        err += '{}与JS-NJ-GL-CE-3.CDMA.log qos 对比不一致，请查看 {}\n'.format(host_2_name, os.path.join(os.getcwd(), html_path))
        with open(html_path,'w') as fo:
            fo.write(hd.make_file('\n'.join(res_qos2).split('\n'), '\n'.join(res_ce_qos).split('\n')))
            fo.close()
    
    if err == '':
        err = '检查通过'
    return err
    

def isis_bfd(config):
    '''echo "ISIS Configuration"，每个interface下（interface "system"忽略）有bfd-enable ipv4的配置'''

    err = ''
    p_isis = r'(?s)(isis 0.*?\n {8}exit)'

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

    if err == '':
        err = '检查通过'
    return err

def static_route_bfd(config):
    '''echo "Static Route Configuration" 和 vprn 中，每个static-route-entry下有bfd-enable'''

    err = ''
    p_static_route_configuration = r'''(?s)(echo "Static Route Configuration"\n#-{50}.*?\n#-{50})'''
    p_vprn = r'(?s)(vprn (\d{3,7}) .*?\n {8}exit)'
    p_vprn_static_route = r'(?s)((static-route-entry \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}|[a-z0-9]{1,4}:[a-z0-9]{1,4}:[a-z0-9]{1,4}::[a-z0-9]{0,4}/\d{1,2})\n.*?\n {12}exit)'

    res_static_route_configuration = re.search(p_static_route_configuration, config)
    if not res_static_route_configuration:
        err = '没有找到Static Route Configuration，请检查\n'

    p_static_route_entry = r'(?s)((static-route-entry \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}|[a-z0-9]{1,4}:[a-z0-9]{1,4}:[a-z0-9]{1,4}::[a-z0-9]{0,4}/\d{1,2}).*?\n {8}exit)'
    res_static_route_entry = re.findall(p_static_route_entry, res_static_route_configuration.group())

    if res_static_route_entry == []:
        err += 'Static Route Configuration 中没有找到static-route，请检查\n'

    for item in res_static_route_entry:
        if 'bfd-enable' not in item[0] and 'black-hole' not in item[0]:
            err += 'Static Route Configuration {} 中没有找到bfd-enable，请检查\n'.format(item[1])

    res_vprn = re.findall(p_vprn, config)
    for vprn in res_vprn:
        res_vprn_static_route = re.findall(p_vprn_static_route, vprn[0])
        for vprn_static_route in res_vprn_static_route:
            if 'bfd-enable' not in vprn_static_route[0] and 'black-hole' not in vprn_static_route[0]:
                err += 'vprn {} {} 中没有找到bfd-enable，请检查\n'.format(vprn[1], vprn_static_route[1])

    if err == '':
        err = '检查通过'
    return err


def bgp_bfd(config):
    '''bgp下面5行内匹配到group的，都要在15行内匹配到bfd-enable'''

    err = ''
    p_bgp = r'(?s)(bgp.*?\n {8}exit)'
    p_gruop = r'(?s)((group ".*?").*?\n {16}exit)'

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
            err += 'BGP Configuration {} 中没有发现bfd-enable\n'.format(item[1])

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
                    if address_1_more:
                        err += '{}比{} 多出的address\n\n{}\n\n'.format(host_1_name, host_2_name, '\n'.join(address_1_more))

                    if address_2_more:
                        err += '{}比{} 多出的address\n\n{}\n\n'.format(host_2_name, host_1_name, '\n'.join(address_2_more))

                break

    #两个检查之间区分
    err += '\n\n'
    
    #找到有exact的address
    p_exact_address = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}|[a-z0-9]{1,4}:[a-z0-9]{1,4}:[a-z0-9]{1,4}::[a-z0-9]{0,4}/\d{1,3}) exact'
    for item in res_prefix_list:
        if item[1].endswith('-IN"') or item[1].endswith('-in"'):
            continue
        res_exact_address = re.findall(p_exact_address, item[0])
        for item2 in res_exact_address:
            if 'static-route-entry {}'.format(item2) not in config:
                err += '{} {} 中的 {} 没有对应 static-route-entry，请检查\n'.format(host_1_name, item[1], item2)

    for item in res_prefix_list2:
        if item[1].endswith('-IN"') or item[1].endswith('-in"'):
            continue
        res_exact_address = re.findall(p_exact_address, item[0])
        for item2 in res_exact_address:
            if 'static-route-entry {}'.format(item2) not in config:
                err += '{} {} 中的 {} 没有对应 static-route-entry，请检查\n'.format(host_2_name, item[1], item2)

    if err == '':
        err = '检查通过'
    return err

def ip_filter_200(config1, config2):
    '''对比JS-NJ-GL-CE-3.CDMA（115.168.128.180），要求ip-filter 200完全一致
    interface下一行description中含有163的，在10行内要有filter ip 200'''

    err = ''
    config_ce = open('JS-NJ-GL-CE-3.CDMA.log').read()
    p_filter_ip_200 = r'(?s)(ip-filter 200 create\n.*?\n {8}exit)'
    res_filter_ip_200_1 = re.search(p_filter_ip_200, config1)
    res_filter_ip_200_2 = re.search(p_filter_ip_200, config2)
    res_filter_ip_200_ce = re.search(p_filter_ip_200, config_ce)

    host_1_name = get_host_name(config1)
    host_2_name = get_host_name(config2)

    if not res_filter_ip_200_1:
        err = '{}没有找到ip-filter 200，请检查\n'.format(host_1_name)
        return err

    if not res_filter_ip_200_2:
        err = '{}没有找到ip-filter 200，请检查\n'.format(host_1_name)
        return err

    if not res_filter_ip_200_ce:
        err += 'JS-NJ-GL-CE-3.CDMA 中没有找到ip-filter 200，请检查\n'
        return err

    hd = difflib.HtmlDiff()
    file_path = os.path.join('检查结果', '{}和{}'.format(host_1_name, host_2_name))

    if res_filter_ip_200_1.group() != res_filter_ip_200_ce.group():
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        html_path = os.path.join(file_path, '{}与JS-NJ-GL-CE-3.CDMA.log ip-filter 200 对比检查结果.html'.format(host_1_name))
        err += '{}与JS-NJ-GL-CE-3.CDMA中的ip-filter 200不一致，请查看{}\n'.format(host_1_name, os.path.join(os.getcwd(), html_path))

        with open(html_path,'w') as fo:
            fo.write(hd.make_file(res_filter_ip_200_1.group().split('\n'), res_filter_ip_200_ce.group().split('\n')))
            fo.close()

    if res_filter_ip_200_2.group() != res_filter_ip_200_ce.group():
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        html_path = os.path.join(file_path, '{}与JS-NJ-GL-CE-3.CDMA.log ip-filter 200 对比检查结果.html'.format(host_2_name))
        err += '{}与JS-NJ-GL-CE-3.CDMA中的ip-filter 200不一致，请查看{}\n'.format(host_2_name, os.path.join(os.getcwd(), html_path))

        with open(html_path,'w') as fo:
            fo.write(hd.make_file(res_filter_ip_200_2.group().split('\n'), res_filter_ip_200_ce.group().split('\n')))
            fo.close()


    
    p_interface = r'(?s)(interface "(.*?)".*?\n {12}exit)'

    res_interface = re.findall(p_interface, config1)
    res_interface_2 = re.findall(p_interface, config2)

    if res_interface == []:
        err += '{}没有找到interface，请检查\n'.format(host_1_name)
        return err

    if res_interface_2 == []:
        err += '{}没有找到interface，请检查\n'.format(host_2_name)
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

    for item in res_interface_2:
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
                err += '{} interface "{}" 没有filter ip 200 请检查\n'.format(host_2_name, item[1])

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
    p_next_hop = r'next-hop (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'

    res_vprn = re.findall(p_vprn, config)
    address = []
    for vprn in res_vprn:
        res_static_route = re.findall(p_static_route, vprn[0])
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

    if res_policy_options_config_1.group() == res_policy_options_config_2.group():
        err = '路由发布对比一致\n'
        return err

    hd = difflib.HtmlDiff()

    file_path = os.path.join('检查结果', '{}和{}'.format(host_1_name, host_2_name))

    if not os.path.exists(file_path):
        os.makedirs(file_path)

    html_path = os.path.join(file_path, '{}与{}路由发布对比检查结果.html'.format(host_1_name, host_2_name))

    with open(html_path,'w') as fo:
        fo.write(hd.make_file(res_policy_options_config_1.group().split('\n'), res_policy_options_config_2.group().split('\n')))
        fo.close()

    err += '{}与{}路由发布对比不一致，请打开 {} 查看\n'.format(host_1_name, host_2_name, os.path.join(os.getcwd(),html_path))

    return err

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
        err = '{}中没有找到System Security Cpm请检查'.format(host_1_name)
        return err

    if not res_config_2_cpm_filter:
        err = '{}中没有找到System Security Cpm请检查'.format(host_2_name)
        return err

    if not res_config_1_system_address:
        err = '{}中没有找到System 地址请检查'.format(host_2_name)
        return err

    if not res_config_2_system_address:
        err = '{}中没有找到System 地址请检查'.format(host_2_name)
        return err
    

    config_1_cpm_filter = res_config_1_cpm_filter.group().replace(res_config_1_system_address.group(2), res_config_1_system_address.group(2) + ' #python标注system地址')
    config_2_cpm_filter = res_config_2_cpm_filter.group().replace(res_config_2_system_address.group(2), res_config_2_system_address.group(2) + ' #python标注system地址')


    if config_1_cpm_filter != config_2_cpm_filter:

        hd = difflib.HtmlDiff()

        file_path = os.path.join('检查结果', '{}和{}'.format(host_1_name, host_2_name))

        if not os.path.exists(file_path):
            os.makedirs(file_path)

        html_path = os.path.join(file_path, '{}与{} cpm-filter对比检查结果.html'.format(host_1_name, host_2_name))
        err += '{}与{} cpm-filter 对比不一致，请打开 {} 查看\n'.format(host_1_name, host_2_name, os.path.join(os.getcwd(),html_path))

        with open(html_path,'w', encoding='utf-8') as fo:
            fo.write(hd.make_file(config_1_cpm_filter.split('\n'), config_2_cpm_filter.split('\n')))
            fo.close()

    if err == '':
        err = '检查通过'

    return err
    

def get_host_name(config):
    '''获取设备名称'''

    p_host_name = r'(?s)(system\n {8}name "(.*?)")'
    res_host_name = re.search(p_host_name, config)
    if not res_host_name:
        host_name = ''
    else:
        host_name = res_host_name.group(2)

    return host_name