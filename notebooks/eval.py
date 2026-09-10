"""Offline eval helper (open in Jupyter if you want a notebook UI)."""
from ticketroute.train import train

if __name__ == "__main__":
    m = train()
    print(m["disclaimer"])
    print("test dept acc", m["test"]["department"]["accuracy"])
    print("keyword", m["test"]["keyword_baseline_dept_acc"])
    print("P1 recall", m["test"]["p1_recall"])
    print(m["test"]["by_language"])
