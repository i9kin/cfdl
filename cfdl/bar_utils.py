from tqdm import tqdm


class Bar:
    def __init__(self, items, debug=True):
        if debug:
            if len(items) != 0:
                self.bar = tqdm(
                    items,
                    ascii=" ━",
                    bar_format="{percentage:.0f}%|{rate_fmt}| {desc} |\x1b[31m{bar}\x1b[0m| {n_fmt}/{total_fmt} [{elapsed}<{remaining}",
                )
        else:
            self.bar = items
        self.debug = debug

    def __iter__(self):
        return self.bar.__iter__()

    def set_description(self, s):
        if self.debug:
            self.bar.set_description(s)

    def update(self):
        if self.debug:
            self.bar.update()


__all__ = ["Bar"]
