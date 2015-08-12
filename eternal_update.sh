

for i in `seq 1 1000`; do
    echo $i
    ./leader_board.py --add_rank=1 --download
    sleep 500
done
