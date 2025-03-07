# check_all_savs.py

import multiprocessing

PSLF_HINTS = [(0, 'SQLite format'), (8, 'Version')]
PSSE_HINTS = [(0, 'FuP_pHySPCD%')]

def process_line(file, dict_, bad_ls, lock):
    # print(line[:30])
    try:
        try:
            with open(file, 'rb') as fp:
                head = fp.read(16)
                lock.acquire()
                if head not in dict_:
                    dict_[head] = [file]
                else:
                    dict_[head] += [file]
                print('.', end='', flush=True)
                lock.release()
        except FileNotFoundError:
            lock.acquire()
            bad_ls.append(file)
            lock.release()
            pass
    finally:
        try:
            lock.release()
        except RuntimeError:
            pass

def main():
    manager = multiprocessing.Manager()
    dict_ = manager.dict()
    lock_ = manager.Lock()
    list_ = manager.list()
    async_results = []
    count1 = 0
    try:
        with open("all_savs.txt", 'r') as all_sav_fp:
            with multiprocessing.Pool() as pool:
                while line := all_sav_fp.readline().strip():
                    # print(line)
                    if not line.endswith(".sav"):
                        continue
                    async_results.append(pool.apply_async(process_line, args=(line, dict_, list_, lock_)))
                    count1 += 1
                    # if x > 2:
                    #     break
                # the wait has to happen in the pool scope
                for ar in async_results:
                    ar.wait()
    except KeyboardInterrupt:
        pass
    print()
    print("total savs", count1)

    count2 = 0
    print_lines = []
    for head, ls in dict_.items():
        # bytes.decode()
        # head = head.decode()
        # print(head)
        hex_ = head.hex(' ')
        str_ = ''
        for h in hex_.split(' '):
            try:
                c = bytes.fromhex(h).decode()
                if c.isspace() or ord(c) < 32 or ord(c) == 127:
                    str_ += ' '
                else:
                    str_ += c
            except:
                str_ += ' '
        best_file = [file for file in ls if '$Recycle.Bin' not in file]
        if best_file:
            best_file = best_file[0]
        else:
            best_file = ls[0]
        print_lines.append((hex_, str_, f'{len(ls):<6}', best_file))
        count2 += len(ls)
    
    print_lines.sort(key=lambda x: x[1], reverse=True)
    for print_line in print_lines:
        print(' | '.join(print_line))

    print("total savs", count2)
    print("skipped", len(list_))
    print(count2 + len(list_))

    # for head, ls in dict_.items():
        
        


if __name__ == '__main__':

    multiprocessing.freeze_support()
    main()
