<?php
require 'store.php';

switch ($action) {
    case 'list':
        route_zones(1);
        break;
    case 'count':
    case 'total':
        echo count([]);
        break;
}
