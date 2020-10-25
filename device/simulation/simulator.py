from tkinter import Frame, Tk, Label
import json
import threading
import time


def crange(c1, c2):
    for c in range(ord(c1), ord(c2) + 1):
        yield chr(c)


def read_simulation_data():
    with open("simulation_data.json", 'r', encoding='utf-8') as file:
        # print(file.read())
        # file.seek(0)
        while True:
            try:
                json_data = json.load(file)
            except Exception:
                pass
            else:
                break
    chips = dict()
    for chip_address in json_data.keys():
        chips[chip_address] = dict()
        chips[chip_address]['locked'] = (
            (json_data[chip_address][0] & 0b10000) > 0
        )
        chips[chip_address]['fuses'] = list()
        for reg_address in range(20, 24):
            for subreg in range(4):
                chips[chip_address]['fuses'].append(
                    (
                        json_data[chip_address][reg_address] & 1 << (
                            2 * subreg)
                    ) > 0
                )
    return chips


class Window(Frame):

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master = master
        self._locked_labels = list()
        self._fuse_labels = list()
        self._place_controls()

    def _place_controls(self):
        chips = read_simulation_data()

        for c_idx, (chip, letter) in enumerate(zip(chips, crange('A', 'C'))):
            l_label = Label(
                self.master, text="L", bg="#ff0000"
            )
            l_label.grid(
                row=c_idx, column=0, padx=2, pady=2
            )
            self._locked_labels.append(l_label)
            self._fuse_labels.append(list())
            for col in range(1, 17):
                f_label = Label(
                    self.master, text=f"{letter}{col - 1}",
                    bg="#ff0000"
                )
                f_label.grid(
                    row=c_idx, column=col, padx=2, pady=2
                )
                self._fuse_labels[c_idx].append(f_label)

    def update_controls(self):
        time.sleep(2)
        while True:
            chips = read_simulation_data()
            for chip, locked_label, fuse_labels in zip(
                chips.values(), self._locked_labels, self._fuse_labels
            ):
                locked_label['bg'] = "#ff0000" if chip['locked'] else "#00ff00"
                locked_label['text'] = "L" if chip['locked'] else "U"
                for fuse, fuse_label in zip(chip['fuses'], fuse_labels):
                    fuse_label['bg'] = "#ff0000" if not fuse else "#00ff00"
            time.sleep(0.05)


def main():
    root = Tk()
    app = Window(root)
    root.wm_title("Rocket Launcher Simulator")
    thread = threading.Thread(target=app.update_controls, daemon=True)
    thread.start()
    root.mainloop()


if __name__ == "__main__":
    main()
