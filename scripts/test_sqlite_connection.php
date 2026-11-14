<?php

require_once __DIR__ . '/../vendor/autoload.php';

putenv('DB_CONNECTION=sqlite');
putenv('DB_SQLITE_PATH=' . __DIR__ . '/../database/database.sqlite');
$_ENV['DB_CONNECTION'] = 'sqlite';
$_ENV['DB_SQLITE_PATH'] = __DIR__ . '/../database/database.sqlite';

try {
    echo "1. Bootstrapping dependencies...\n";
    require_once __DIR__ . '/../src/Shared/Infrastructure/dependencies.php';
    echo "   Connected to SQLite and initialized DI container!\n";

    echo "2. Testing UserService & UserRepository...\n";
    $users = $userService->getAllUsers();
    echo "   Total users in SQLite: " . count($users) . "\n";
    $sampleUser = $users[0];
    echo "   Sample user: " . $sampleUser->getNombre() . " " . $sampleUser->getApellidos() . " (" . $sampleUser->getEmail() . ", Rol: " . $sampleUser->getRol()->value . ")\n";

    echo "3. Testing ServicioService...\n";
    $servicios = $servicioService->getAllServices();
    echo "   Total servicios: " . count($servicios) . "\n";
    foreach (array_slice($servicios, 0, 3) as $s) {
        echo "   - " . $s->getNombreServicio() . " (" . $s->getPrecio() . "€, " . $s->getDuracionMinutos() . " min)\n";
    }

    echo "4. Testing EspecialistaService...\n";
    $especialistas = $especialistaService->getAllEspecialistas();
    echo "   Total especialistas: " . count($especialistas) . "\n";
    foreach (array_slice($especialistas, 0, 3) as $e) {
        echo "   - ID: " . $e->idEspecialista . ": " . $e->nombre . " " . $e->apellidos . " (" . $e->descripcion . ")\n";
    }

    echo "5. Testing ReservaService...\n";
    $count = $reservaService->countAllReservasWithFilters();
    echo "   Total reservas count: " . $count . "\n";
    $reservas = $reservaService->getAllReservasWithFilters([], 5, 0);
    echo "   Fetched " . count($reservas) . " sample reservas.\n";
    if (count($reservas) > 0) {
        $r = $reservas[0];
        echo "   Sample reserva: ID {$r->id_reserva} - Cliente {$r->cliente_nombre} {$r->cliente_apellidos} con {$r->especialista_nombre} ({$r->nombre_servicio})\n";
        echo "   Fecha: {$r->fecha_reserva} {$r->hora_inicio} - Estado: {$r->estado}\n";
    }

    echo "6. Testing PasswordResetRepository...\n";
    $userByToken = $passwordResetRepository->getUserByResetToken('non_existent_token');
    echo "   getUserByResetToken executed without error (Result: " . ($userByToken ? 'User' : 'null') . ").\n";

    echo "\n==================================================\n";
    echo " SUCCESS: All application services pass with SQLite!\n";
    echo "==================================================\n";
} catch (\Throwable $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
    echo $e->getTraceAsString() . "\n";
    exit(1);
}
