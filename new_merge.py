# -*- coding: utf-8 -*-
"""
Created on Thu Jul 21 02:58:12 2016

@author:
"""

import time
import os
import random
import merge as mg
import cPickle as cP
from multiprocessing import Pool
from optimize_route import opt_route
from main_lp import load_routes, dump_routes, process_pro

PROCESSORS = 20


def merge_two(r):
    global allo, o2o_mini
    opt_str, obj = opt_route(r, allo, o2o_mini)
    return opt_str


f1 = open('allo', 'rb')
allo = cP.load(f1)
f1.close()
o2o_mini = mg.generate_o2o_minimum_start(allo)

if __name__ == '__main__':
    # Multiprocessing
    # loc, allo = loadData.loadData('../original_data')
    # parameters for self evolve
    rounds = 0
    pairs_num = 5000
    # parameters for interactions
    inter_rounds = 25
    inter_pairs_num = 10000
    inter_prob_o2o = 0.7
    inter_prob_dif = 0.8
    # parameters for random merge
    rnd_rounds = 10
    rnd_pairs_num = 5000
    rnd_prob_o2o, rnd_prob_new = 0.3, 0.4
    # multiprocessing
    pool = Pool(PROCESSORS, process_pro)
    # Site and O2O evolve themselves
    # read files:
    site_f_name, o2o_f_name, new_f_name, total_f_name = 'site_re', 'o2o_re', 'new_re', 'total_re'
    print('reading files...')
    site_set = load_routes(site_f_name, need_decompression=False)
    site_num = len(site_set)
    print('Site complete with num: ' + str(site_num))
    o2o_set = load_routes(o2o_f_name, need_decompression=False)
    o2o_num = len(o2o_set)
    print('O2O complete with num: ' + str(o2o_num))
    new_set = load_routes(new_f_name, need_decompression=False)
    new_num = len(new_set)
    print('New complete with num: ' + str(new_num))
    total_set = load_routes(total_f_name, is_set=True)
    total_num = len(total_set)
    print('Total complete with num: ' + str(total_num))
    stime = time.time()
    # Start rounds:
    # pool = Pool(PROCESSORS, process_init, (allo, ))
    # TBC...........................................................
    now_r = 0
    isD = False
    while now_r < rounds:
        isD = True
        now_r += 1
        print('Start rounds ' + str(now_r) + '. Generating pairs')
        site_pairs = [(random.choice(site_set), random.choice(site_set)) for i in range(pairs_num)]
        o2o_pairs = [(random.choice(o2o_set), random.choice(o2o_set)) for i in range(pairs_num)]
        print('Generating complete. Now merge site')
        site_add_len = 0
        site_ms = pool.map(merge_two, site_pairs)
        print('Site merge complete. Now delete replicate and add to site set and total set')
        for si_m in site_ms:
            for site_r in si_m:
                if not (site_r in total_set):
                    site_add_len += 1
                    site_set.append(site_r)
                    total_set.add(site_r)
        print('Site completed. New site: ' + str(site_add_len))
        print('Start merge O2O')
        o2o_ms = pool.map(merge_two, o2o_pairs)
        print('o2o merge complete. Now del and add')
        o2o_add_len = 0
        for o_m in o2o_ms:
            for o_str in o_m:
                if not (o_str in total_set):
                    o2o_add_len += 1
                    o2o_set.append(o_str)
                    total_set.add(o_str)
        print('O2O completed. New O2O: ' + str(o2o_add_len))
        print('Round ' + str(now_r) + 'end.')
        if time.time() - stime > 20 * 60:
            dump_routes('site_set', site_set, is_compressed=True)
            dump_routes('o2o_set', o2o_set, is_compressed=True)
            dump_routes('total_set', total_set, is_set=True)
            print('Dump completed, next round')
            stime = time.time()
    if isD:
        dump_routes('site_set', site_set, is_compressed=True)
        dump_routes('o2o_set', o2o_set, is_compressed=True)
        dump_routes('total_set', total_set, is_set=True)
        print('Dump completed, self evolve end')

    # Set and O2O interaction
    now_r = 0
    stime = time.time()
    isD = False
    while now_r < inter_rounds:
        isD = True
        now_r += 1
        print('Start interaction round ' + str(now_r) + '. Generating pairs')
        inter_pairs, inter_types = [], []
        # inter_type: 0 interaction, 1 site, 2 o2o
        now_p = 0
        while now_p < inter_pairs_num:
            now_p += 1
            this_type = 0
            if random.random() < inter_prob_o2o:
                # pick one from O2O orders
                fpic = random.choice(o2o_set)
                if random.random() < inter_prob_dif:
                    # pick one from site orders
                    spic = random.choice(site_set)
                    this_type = 0
                else:
                    # pick one from o2o orders
                    spic = random.choice(o2o_set)
                    this_type = 2
            else:
                # pick one from site orders
                fpic = random.choice(site_set)
                if random.random() < inter_prob_dif:
                    # pick from o2o
                    spic = random.choice(o2o_set)
                    this_type = 0
                else:
                    # pick from site
                    spic = random.choice(site_set)
                    this_type = 1
            inter_pairs.append((spic, fpic))
            inter_types.append(this_type)
        print('Generate ' + str(len(inter_pairs)) + ' completed! Now start to merge...')
        site_add_len, o2o_add_len, new_add_len = 0, 0, 0
        inter_m_res = pool.map(merge_two, inter_pairs)
        print('Merge complete... Now del and add')
        for inter_m, inter_t in zip(inter_m_res, inter_types):
            if inter_t == 0:
                # interaction
                for inter_str in inter_m:
                    if not (inter_str in total_set):
                        new_add_len += 1
                        new_set.append(inter_str)
                        total_set.add(inter_str)
            elif inter_t == 2:
                # o2o
                for o2o_str in inter_m:
                    if not (o2o_str in total_set):
                        o2o_add_len += 1
                        o2o_set.append(o2o_str)
                        total_set.add(o2o_str)
            else:
                # site
                for site_str in inter_m:
                    if not (site_str in total_set):
                        site_add_len += 1
                        site_set.append(site_str)
                        total_set.add(site_str)
        print('Add complete.')
        print('New added: ' + str(new_add_len))
        print('Site added: ' + str(site_add_len))
        print('O2O added: ' + str(o2o_add_len))
        print('Round ' + str(now_r) + 'end..')
        if time.time() - stime > 30 * 60:
            dump_routes('site_set', site_set, is_compressed=True)
            dump_routes('o2o_set', o2o_set, is_compressed=True)
            dump_routes('new_set', new_set, is_compressed=True)
            dump_routes('total_set', total_set, is_set=True)
            print('Dump completed, next round')
            stime = time.time()
    if isD:
        dump_routes('site_set', site_set, is_compressed=True)
        dump_routes('o2o_set', o2o_set, is_compressed=True)
        dump_routes('new_set', new_set, is_compressed=True)
        dump_routes('total_set', total_set, is_set=True)
        print('Dump completed, interaction end.')

    # Start random merge process
    now_r = 0
    stime = time.time()
    while now_r < rnd_rounds:
        now_r += 1
        print('Start rnd merge round ' + str(now_r))
        rnd_pairs, rnd_types = [], []
        now_p = 0
        while now_p < rnd_pairs_num:
            now_p += 1
            this_type = 0
            # type: 0 inter, 1 site, 2 o2o
            f_p_r = random.random()
            s_p_r = random.random()
            f_p_t, s_p_t = 0, 0
            if f_p_r < rnd_prob_o2o:
                # fpick o2o order
                fpic = random.choice(o2o_set)
                f_p_t = 2
            elif f_p_r < rnd_prob_o2o + rnd_prob_new:
                # fpick inter order
                fpic = random.choice(new_set)
                f_p_t = 0
            else:
                # fpick site order
                fpic = random.choice(site_set)
                f_p_t = 1
            if s_p_r < rnd_prob_o2o:
                # spick o2o order
                spic = random.choice(o2o_set)
                s_p_t = 2
            elif s_p_r < rnd_prob_o2o + rnd_prob_new:
                # spick inter order
                spic = random.choice(new_set)
                s_p_t = 0
            else:
                # spick site order
                spic = random.choice(site_set)
                s_p_t = 1
            rnd_pairs.append((fpic, spic))
            if f_p_t == 2 == s_p_t:
                this_type = 2
            elif f_p_t == 1 == s_p_t:
                this_type = 1
            else:
                this_type = 0
            rnd_types.append(this_type)
        print('Generate ' + str(len(rnd_pairs)) + ' completed. Now start to merge...')
        site_add_len, o2o_add_len, new_add_len = 0, 0, 0
        rnd_m_res = pool.map(merge_two, rnd_pairs)
        print('Merge complete. Del and add')
        for rnd_m, rnd_t in zip(rnd_m_res, rnd_types):
            if rnd_t == 0:
                # inter
                for rnd_str in rnd_m:
                    if not (rnd_str in total_set):
                        new_add_len += 1
                        new_set.append(rnd_str)
                        total_set.add(rnd_str)
            elif rnd_t == 2:
                # o2o
                for rnd_str in rnd_m:
                    if not (rnd_str in total_set):
                        o2o_add_len += 1
                        o2o_set.append(rnd_str)
                        total_set.add(rnd_str)
            else:
                # site
                for rnd_str in rnd_m:
                    if not (rnd_str in total_set):
                        site_add_len += 1
                        site_set.append(rnd_str)
                        total_set.add(rnd_str)
        print('Add complete.')
        print('New added: ' + str(new_add_len))
        print('Site added: ' + str(site_add_len))
        print('O2O added: ' + str(o2o_add_len))
        print('Round ' + str(now_r) + 'end..')
        if time.time() - stime > 30 * 60:
            dump_routes('site_set', site_set, is_compressed=True)
            dump_routes('o2o_set', o2o_set, is_compressed=True)
            dump_routes('new_set', new_set, is_compressed=True)
            dump_routes('total_set', total_set, is_set=True)
            print('Dump completed, next round')
            stime = time.time()
    dump_routes('site_set', site_set, is_compressed=True)
    dump_routes('o2o_set', o2o_set, is_compressed=True)
    dump_routes('new_set', new_set, is_compressed=True)
    dump_routes('total_set', total_set, is_set=True)
    print('Dump completed, rnd end.')

    os.system("pause")