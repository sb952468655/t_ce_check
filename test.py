import re
from check import ip_filter_200

c = r'''prefix-list "route-to-AAA-master-IN"
                prefix 0.0.0.0/0 exact
                prefix 10.76.0.0/16 longer
                prefix 10.77.0.0/16 longer
                prefix 117.61.0.0/16 longer
                prefix 180.98.0.0/16 longer
                prefix 180.99.0.0/16 longer
            exit'''


p_prefix_list = r'(?s)(prefix-list "(.*?-IN)"\n.*?\n {12}exit)'

res = re.search(p_prefix_list, c)

if res:
    print(res.group())


