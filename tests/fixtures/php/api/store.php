<?php
class Store {
    public function save($x) {
        return $this->check($x);
    }

    private function check($x) {
        return $x;
    }
}

function route_zones($db) {
    $s = new Store();
    return $s->save($db);
}
