let app = angular.module('app', []);
app.factory('apiService', ['$http', $http => new ApiService($http)]);

function Device(data) {
    Object.assign(this, data);

    this.addresses = function () {
        return data.addr_info
            .filter((addr) => addr.family === "inet").map(addr => addr.local)
            .join(', ')
    }
}

function Wifi(data) {
    Object.assign(this, data);
    this.signal_level = parseInt(data['signal_level'])

    /*
    -30 dBm 	Amazing 	Max achievable signal strength. The client can only be a few feet from the AP to achieve
                            this. Not typical or desirable in the real world. 	N/A
    -67 dBm 	Very Good 	Minimum signal strength for applications that require very reliable, timely delivery of data
                            packets. 	VoIP/VoWiFi, streaming video
    -70 dBm 	Okay 	    Minimum signal strength for reliable packet delivery. 	Email, web
    -80 dBm 	Not Good 	Minimum signal strength for basic connectivity. Packet delivery may be unreliable. 	N/A
    -90 dBm 	Unusable 	Approaching or drowning in the noise floor. Any functionality is highly unlikely. 	N/A
     */
    this.strength_thresholds = [30, 67, 70, 80, 90]

    this.strength = -1;
    for (let i = 0; i < this.strength_thresholds.length; i++) {
        let th = this.strength_thresholds[i];
        console.log('checking', Math.abs(this.signal_level), 'against', th)
        if (Math.abs(this.signal_level) <= th) {
            this.strength = i;
            break;
        }
    }

    this.strength_class = function () {
        switch (this.strength) {
            case -1:
                return 'grey-text';
            case 0:
            case 1:
                return 'green-text';
            case 2:
                return 'yellow-text'
            case 3:
                return 'orange-text'
            default:
                return 'red_text'

        }
    }
}

ApiService = function ($http) {
    console.debug('creating ApiService');

    const $this = this;

    this.loadServices = function () {
        return $http.get('/api/services')
            .then(function successCallback(response) {
                return response['data'];
            }, function errorCallback(response) {
                console.error(response);
            });
    };

    this.loadNetworks = function () {
        return $http.get('/api/wifi/scan')
            .then(function successCallback(response) {
                return response['data'].map(record => new Wifi(record));
            }, function errorCallback(response) {
                console.error(response);
            });
    };

    this.loadWifiStatus = function () {
        return $http.get('/api/wifi/status')
            .then(function successCallback(response) {
                return response['data'];
            }, function errorCallback(response) {
                console.error(response);
            });
    };

    this.loadDevices = function () {
        return $http.get('/api/devices')
            .then(function successCallback(response) {
                return response['data']
                    .filter(record => record.ifname !== 'lo')
                    .map(record => new Device(record));
            }, function errorCallback(response) {
                console.error(response);
            });
    };

    this.loadIpInfo = function () {
        return $http.get('/api/ipinfo')
            .then(function successCallback(response) {
                return response['data'];
            }, function errorCallback(response) {
                console.error(response);
            });
    };

    this.loadHealth = function () {
        return $http.get('/api/health')
            .then(function successCallback(response) {
                return response['data'];
            }, function errorCallback(response) {
                console.error(response);
            });
    };

    this.loadLogFile = function (service) {
        return $http.get('/api/services/' + service + '/log')
            .then(function successCallback(response) {
                return response['data'];
            }, function errorCallback(response) {
                console.error(response);
            });
    }

    this.doRestartService = function (service) {
        return $http.put('/api/services/' + service + '/running')
    }

}

AppController = function ($scope, $http, $timeout, $interval, apiService) {
    console.debug("creating AppController");
    const $this = this;

    $this.servicesFilter = [/openvpn-client@.*/, /dnsmasq/, /hostapd/];

    $scope.services = [];
    $scope.devices = [];
    $scope.networks = [];
    $scope.wifi_status = {};
    $scope.ipinfo = {};
    $scope.health = {};

    $scope.restartButtonDisabled = false;

    $scope.restartVpn = function () {
        $scope.restartButtonDisabled = true;
        apiService.doRestartService("openvpn-client@vpnbox")
            .then(response => {
                console.error("Restarting VPN");
                $scope.restartButtonDisabled = false;
            }, error => {
                console.error("Error restarting service", error);
                M.toast({html: 'Error restarting VPN'});
                $scope.restartButtonDisabled = false;
            });
    }

    $scope.get_flag = function (code) {
        return get_country(code).emoji;
    }

    apiService.loadServices().then((services) => {
        $scope.services = services.filter((service) => {
            for (let i = 0; i < $this.servicesFilter.length; i++) {
                const filter = $this.servicesFilter[i];
                const serviceName = service.Id.replace('.service', '')
                if (serviceName.match(filter)) {
                    console.debug(serviceName, 'matches', filter);
                    return true;
                }
            }
            return false;
        });
    });

    apiService.loadHealth().then((data) => {
        $scope.health = data;
    });
    apiService.loadDevices().then((devices) => {
        $scope.devices = devices;
    });
    apiService.loadNetworks().then((networks) => {
        $scope.networks = networks;
    });
    apiService.loadWifiStatus().then((status) => {
        $scope.wifi_status = status;
    });
    apiService.loadIpInfo().then((info) => {
        $scope.ipinfo = info;
    });
    apiService.loadLogFile('openvpn-client@*.service').then((data) => {
        $scope.log = data;
    });
}

console.debug('starting app module');
angular.module('app').controller('AppController', [
    '$scope', '$http', '$timeout', '$interval', 'apiService', AppController
]);

