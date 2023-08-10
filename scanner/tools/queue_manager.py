def get_next_item_from_queue(self, page_name):
    for index, info in enumerate(self.data_queue):
        if info[1] == page_name:
            data = self.data_queue.pop(index)[0]
            break
    else:
        index = -1
        while self.data_queue[index][1] == self.data_queue[index - 1][1]:
            if -(index - 1) < len(self.data_queue):
                index -= 1
            else:
                data = self.data_queue.pop(index)[0]
                break
        else:
            data = self.data_queue.pop(index)[0]
    return data
