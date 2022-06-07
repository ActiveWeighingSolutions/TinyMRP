import * as THREE from './build/three.module.js';
import { OrbitControls } from './examples/jsm/controls/OrbitControls.js';

import { STLLoader } from './examples/jsm/loaders/STLLoader.js';
import { ThreeMFLoader } from './examples/jsm/loaders/3MFLoader.js';
import { OBJLoader } from './examples/jsm/loaders/OBJLoader.js';



export function main(path) {

    const offset = 0;


    const canvas = document.querySelector('#c');
    const renderer = new THREE.WebGLRenderer({ canvas });


    
    const fov = 450;
    const aspect = 2;  // the canvas default
    const near = 0.1;
    const far = 100;
    const camera = new THREE.PerspectiveCamera(fov, aspect, near, far);
    camera.position.set(0, 10, 20);
    const orbitControls = new OrbitControls(camera, canvas);
    orbitControls.target.set(5, 5, 0);
    orbitControls.update();

    const scene = new THREE.Scene();
    scene.background = new THREE.Color('white');

    const loader3 = new ThreeMFLoader();

    var objeto = new THREE.Object3D();
    var size = new THREE.Vector3();
 

    loader3.load(path, function (object3mf) {
        
        /*object3mf.scale.set(0.1, 0.1, 0.1);*/
        /*objeto = object3mf*/
        const boundingBox = new THREE.Box3();
        boundingBox.setFromObject(object3mf);

        var middle = new THREE.Vector3();
                
        boundingBox.getSize(size);

        const fov = camera.fov * (Math.PI / 180);
        const fovh = 2 * Math.atan(Math.tan(fov / 2) * camera.aspect);
        let dx = size.z / 2 + Math.abs(size.x / 2 / Math.tan(fovh / 2));
        let dy = size.z / 2 + Math.abs(size.y / 2 / Math.tan(fov / 2));
        let cameraZ = Math.max(dx, dy);
        

        // offset the camera, if desired (to avoid filling the whole canvas)
        if (offset !== undefined && offset !== 0) cameraZ *= offset;

        camera.position.set(0, 0, cameraZ);

        // set the far plane of the camera so that it easily encompasses the whole object
        const minZ = boundingBox.min.z;
        const cameraToFarEdge = (minZ < 0) ? -minZ + cameraZ : cameraZ - minZ;

        camera.far = cameraToFarEdge * 3;
        camera.updateProjectionMatrix();

        if (orbitControls !== undefined) {
            // set camera to rotate around the center
            orbitControls.target = new THREE.Vector3(0, 0, 0);

            // prevent camera from zooming out far enough to create far plane cutoff
            orbitControls.maxDistance = cameraToFarEdge * 2;
        }




        scene.add(object3mf);

    });
    
 

    //alert(100000000 * size.x + 100000 * size.y + size.z);


    


   

    

    

    //{
    //    const planeSize = 40;

    //    const loader = new THREE.TextureLoader();
    //    const texture = loader.load('https://threejsfundamentals.org/threejs/resources/images/checker.png');
    //    texture.wrapS = THREE.RepeatWrapping;
    //    texture.wrapT = THREE.RepeatWrapping;
    //    texture.magFilter = THREE.NearestFilter;
    //    const repeats = planeSize / 2;
    //    texture.repeat.set(repeats, repeats);

    //    const planeGeo = new THREE.PlaneGeometry(planeSize, planeSize);
    //    const planeMat = new THREE.MeshPhongMaterial({
    //        map: texture,
    //        side: THREE.DoubleSide,
    //    });
    //    const mesh = new THREE.Mesh(planeGeo, planeMat);
    //    mesh.rotation.x = Math.PI * -.5;
    //    scene.add(mesh);
    //}



    {
        const skyColor = 0xB1E1FF;  // light blue
        const groundColor = 0xB97A20;  // brownish orange
        const intensity = 1;
        const light = new THREE.HemisphereLight(skyColor, groundColor, intensity);
        scene.add(light);
    }

    {
        const color = 0xFFFFFF;
        const intensity = 0.51;
        const light = new THREE.DirectionalLight(color, intensity);
        light.position.set(10, 10, 10);
        light.target.position.set(0, 0, 0);
        scene.add(light);
        scene.add(light.target);
    }

   



    function resizeRendererToDisplaySize(renderer) {
        const canvas = renderer.domElement;
        const width = canvas.clientWidth;
        const height = canvas.clientHeight;
        const needResize = canvas.width !== width || canvas.height !== height;
        if (needResize) {
            renderer.setSize(width, height, false);
        }
        return needResize;
    }

    function render() {

        if (resizeRendererToDisplaySize(renderer)) {
            const canvas = renderer.domElement;
            camera.aspect = canvas.clientWidth / canvas.clientHeight;
            camera.updateProjectionMatrix();
        }

        renderer.render(scene, camera);

        requestAnimationFrame(render);
    }

    requestAnimationFrame(render);
}
 

/*var file = {{ path | tojson}};*/
//var file = './static/images/logo.3MF';
//main(file);