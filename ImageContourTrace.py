# conding: utf-8

import PIL.Image
import sys, os, datetime


class ImageContuorTrace:
    """
    画像輪郭トレース
    """

    def __init__(self, args):
        """
        初期化
        """

        self.action_mode = 0

        arg_cnt = len(args)
        if arg_cnt == 1:
            self.action_mode = 0
        elif arg_cnt == 2:
            self.action_mode = 1
            self.input_image_file_path = args[1]
        elif arg_cnt >= 3:
            self.input_image_file_path = args[1]
            input_mode = args[2]

            if input_mode == '1':
                self.action_mode = 11
                self.input_color_r = args[3]
                self.input_color_g = args[4]
                self.input_color_b = args[5]
                self.input_color_range = args[6]

        self.is_debug = True


    def main(self):
        """
        メイン処理
        """

        if self.action_mode == 0:
            txt = "引数が指定されていません。処理を終了します。"
            txt += "press any key"
            a = input(txt)
        elif self.action_mode == 11:
            self.make_image_contuor_trace_info()

    def make_image_contuor_trace_info(self):
        """
        画像輪郭トレース情報作成
        """

        t1 = datetime.datetime.now()

        self.im = PIL.Image.open(self.input_image_file_path).convert('RGB')
        self.im_size_x = self.im.size[0]
        self.im_size_y = self.im.size[1]

        color_range = int(self.input_color_range)

        self.target_rgb_range_lower = (int(self.input_color_r) - color_range, int(self.input_color_g) - color_range, int(self.input_color_b) - color_range)
        self.target_rgb_range_upper = (int(self.input_color_r) + color_range, int(self.input_color_g) + color_range, int(self.input_color_b) + color_range)

        # 追跡済み情報
        self.set_pixel_tracked = set()

        # 発見した輪郭情報
        self.list_discover = []

        # 輪郭検索方向情報
        self.dic_search_direct = self.get_search_direct()

        # デバッグ：画像出力準備
        if self.is_debug:self.im3 = PIL.Image.new('RGB',(self.im_size_x, self.im_size_y))

        # 検出開始
        for y in range(self.im_size_y):
            for x in range(self.im_size_x):
                r, g, b = self.im.getpixel((x, y))

                if self.check_color_range(r, g, b):
                    if (x, y) not in self.set_pixel_tracked:

                        # 輪郭追跡
                        if self.is_debug:print("target:", x, y)
                        self.contour_tracking(x, y)

        # デバッグ：画像出力準備
        if self.is_debug:self.im3.save(os.path.join(os.path.dirname(self.input_image_file_path),'im3_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '_' + self.input_color_r.rjust(3) + '_' + self.input_color_g.rjust(3) + '_' + self.input_color_b.rjust(3) + '_' + self.input_color_range + '.bmp'), 'bmp')

        # 情報出力
        self.write_info()

        t2 = datetime.datetime.now()
        print("所要時間：" + str(t2 - t1))

    def get_search_direct(self):
        return {
            0:(-1,1), 1:(0,1), 2:(1,1), 3:(1,0)
            , 4:(1,-1), 5:(0,-1), 6:(-1,-1), 7:(-1,0)
            , 8:(-1,1), 9:(0,1), 10:(1,1), 11:(1,0)
            , 12:(1,-1), 13:(0,-1), 14:(-1,-1), 15:(-1,0)
        }

    def contour_tracking(self, x, y):
        """
        輪郭追跡
        """
        lst_pos = list()
        search_start_direct = 0

        # 追跡済み記録
        self.set_pixel_tracked.add((x, y))

        # スタート地点記録
        lst_pos.append((search_start_direct, (x, y)))
        set_pos = set([(x,y)])

        x_current = x
        y_current = y
                    
        while True:
            
            direct, pos = self.search_contour(x_current, y_current, search_start_direct)

            if direct == 8:
                break

            x_current = pos[0]
            y_current = pos[1]

            if (direct, (x_current, y_current)) in lst_pos:
                break

            lst_pos.append((direct, (x_current, y_current)))
            if self.is_debug:self.im3.putpixel((x_current, y_current), (0,0,255))
            if self.is_debug:print("  contour", "direct, (x,y):", direct, (x_current, y_current))
            set_pos.add((x_current, y_current))
            search_start_direct = (direct + 6) % 8

        if len(set_pos) > 1:
            # x, y, [(x1,y1),(x2,y2),(x3,y3),(x4,y4)]
            x_pos_min = min([pos[0] for pos in set_pos])
            y_pos_min = min([pos[1] for pos in set_pos])
            x_pos_max = max([pos[0] for pos in set_pos])
            y_pos_max = max([pos[1] for pos in set_pos])
            self.list_discover.append([x, y, x_pos_min, y_pos_min, lst_pos])

            # 追跡済み記録
            for x_trace in range(x_pos_min, x_pos_max + 1):
                for y_trace in range(y_pos_min, y_pos_max + 1):

                    pos = (x_trace, y_trace)
                    r, g, b = self.im.getpixel(pos)
                    if self.check_color_range(r, g, b):
                        self.set_pixel_tracked.add(pos)
                        if self.is_debug:self.im3.putpixel((x_trace, y_trace), (255,0,0))
                        if self.is_debug:print("    area_multi :",x_trace,y_trace)


                # y_trace_start = y_pos_min

                # while y_trace_start <= y_pos_max:
                #     if (x_trace, y_trace_start) in set_pos:
                #         y_trace_from = y_trace_start
                #         is_found = False
                #         for y_trace_track in range(y_trace_from + 1, y_pos_max + 1):
                #             if (x_trace, y_trace_track) in set_pos:
                #                 y_trace_to = y_trace_track
                #                 is_found = True
                #                 break
                #             # else:
                #             #     y_trace_to = y_trace_track
                #             #     break

                #         if is_found:
                #             for y_trace in range(y_trace_from, y_trace_to + 1):
                #                 self.set_pixel_tracked.add((x_trace, y_trace))
                #                 if self.is_debug:self.im3.putpixel((x_trace, y_trace), (255,0,0,127))
                #                 if self.is_debug:print("    area_multi :",x_trace,y_trace)
                #             y_trace_start = y_trace_to + 1
                #         else:
                #             self.set_pixel_tracked.add((x_trace, y_trace_from))
                #             if self.is_debug:self.im3.putpixel((x_trace, y_trace_from), (0,255,0,127))
                #             if self.is_debug:print("    area_single:",x_trace,y_trace_from)
                #             y_trace_start = y_trace_from + 1
                #     else:
                #         y_trace_start += 1

    def search_contour(self, x, y, search_start_direct):
        # 反時計回りに輪郭を検索
        for direct in range(8):
            direct += search_start_direct
            x_search = x + self.dic_search_direct[direct][0]
            y_search = y + self.dic_search_direct[direct][1]
            if x_search >= self.im_size_x or x_search < 0 or y_search >= self.im_size_y or y_search < 0:
                continue
            pos = (x_search, y_search)
            self.set_pixel_tracked.add(pos)
            r, g, b = self.im.getpixel(pos)
            if self.check_color_range(r, g, b):
                return (direct if direct <= 7 else direct - 8), pos
        return 8 ,(0,0)

    def check_color_range(self, r, g, b):
        return (self.target_rgb_range_lower[0] <= r <= self.target_rgb_range_upper[0]) and (self.target_rgb_range_lower[1] <= g <= self.target_rgb_range_upper[1]) and (self.target_rgb_range_lower[2] <= b <= self.target_rgb_range_upper[2])

    def write_info(self):
        txt = []
        for info in self.list_discover:
            txt.append(str(info[0]) + ',' + str(info[1]) + ',' + str(info[2]) + ',' + str(info[3]) + ',' + str(info[4]))
        file_path = os.path.dirname(self.input_image_file_path)
        file_base_name = os.path.splitext(os.path.basename(self.input_image_file_path))[0]
        out_file_path = os.path.join(file_path, file_base_name + '.txt')
        if os.path.exists(out_file_path):os.remove(out_file_path)
        with open(out_file_path, mode='x') as write_file:
            write_file.write('\n'.join(txt))


"""
ファイルとして実行
"""
if __name__ == '__main__':

    # print(len(sys.argv))
    # print(sys.argv)
    # print([type(s) for s in sys.argv])

    # obj = ImageContuorTrace(sys.argv)
    # obj.main()

    args = []
    args.append('')
    args.append(r"C:\work\Python\study\proc_pixel\元画像1.bmp")
    args.append('1')
    args.append('156')
    args.append('192')
    args.append('249')
    args.append('10')
    obj = ImageContuorTrace(args)
    obj.main()


