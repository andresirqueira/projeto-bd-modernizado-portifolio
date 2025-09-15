// Sistema de mapeamento inteligente de imagens de equipamentos
// Usa as imagens existentes em static/img no padrão tipo-marca-modelo.png

const equipmentImageMap = {
  // Speakers
  'speaker': {
    'jbl-cbt': '/static/img/speaker-jbl-jbl-cbt-1000e.png',
    'jbl': '/static/img/speaker-jbl-outro.png',
    'shure-mxn5w-c': '/static/img/speaker-shure-mxn5w-c.png',
    'shure': '/static/img/speaker-shure-mxn5w-c.png',
    'logitech-rally': '/static/img/speaker-logitech-rally.png',
    'logitech': '/static/img/speaker-logitech-rally.png',
    'speaker logitech': '/static/img/speaker-logitech-rally.png',
    'speaker shure': '/static/img/speaker-shure-mxn5w-c.png',
    'speaker jbl': '/static/img/speaker-jbl-outro.png',
    'default': '/static/img/speaker-shure-mxn5w-c.png'
  },
  
  // Microfones
  'microfone': {
    'shure-mxa920': '/static/img/microfone-shure-mxa920.png',
    'shure-mxa910': '/static/img/microfone-shure-mxa910.png',
    'shure-mxa710': '/static/img/microfone-shure-mxa710.png',
    'shure-blx1': '/static/img/microfone-shure-blx1.png',
    'shure-sm58': '/static/img/microfone-shure-sm58.png',
    'logitech-rally-mic-pod': '/static/img/microfone-logitech-rally-mic-pod.png',
    'jabra-speak': '/static/img/microfone-jabra-jabra-speak.png',
    'microfone logitech': '/static/img/microfone-logitech-rally-mic-pod.png',
    'microfone jabra': '/static/img/microfone-jabra-jabra-speak.png',
    'logitech': '/static/img/microfone-logitech-rally-mic-pod.png',
    'jabra': '/static/img/microfone-jabra-jabra-speak.png',
    'default': '/static/img/microfone-shure-mxa920.png'
  },
  
  // Câmeras
  'camera': {
    'logitech-rally': '/static/img/camera-logitech-rally.png',
    'huddly-go': '/static/img/camera-huddly-huddly-go.png',
    'jabra-panacast': '/static/img/camera-jabra-panacast.png',
    'yealink': '/static/img/camera-yealink-outro.png',
    'logitech': '/static/img/camera-logitech-rally.png',
    'huddly': '/static/img/camera-huddly-huddly-go.png',
    'jabra': '/static/img/camera-jabra-panacast.png',
    'default': '/static/img/camera-logitech-rally.png'
  },
  
  // AVIO Dante
  'avio': {
    'dante-2ch-analog-output': '/static/img/avio-dante-2ch-analog-output-adapter.png',
    'dante-2ch-analog-input': '/static/img/avio-dante-2ch-analog-input-adapter.png',
    'dante-1ch-analog-output': '/static/img/avio-dante-1ch-analog-output-adapter.png',
    'dante-1ch-analog-input': '/static/img/avio-dante-1ch-analog-input-adapter.png',
    'dante-2ch-usb-io': '/static/img/avio-dante-2ch-usb-io-adapter.png',
    'dante-usb': '/static/img/avio-dante-2ch-usb-io-adapter.png',
    'dante avio usb': '/static/img/avio-dante-2ch-usb-io-adapter.png',
    'avio usb': '/static/img/avio-dante-2ch-usb-io-adapter.png',
    'dante avio': '/static/img/avio-dante-2ch-usb-io-adapter.png',
    'usb': '/static/img/avio-dante-2ch-usb-io-adapter.png',
    'dante': '/static/img/avio-dante-2ch-analog-output-adapter.png',
    'default': '/static/img/avio-dante-2ch-analog-output-adapter.png'
  },
  
  // Hubs
  'hub': {
    'logitech-display': '/static/img/hub-logitech-display.png',
    'logitech-table': '/static/img/hub-logitech-table.png',
    'logitech-mic-pod': '/static/img/hub-logitech-mic-pod.png',
    'mic-pod': '/static/img/hub-logitech-mic-pod.png',
    'mic pod': '/static/img/hub-logitech-mic-pod.png',
    'logitech': '/static/img/hub-logitech-display.png',
    'default': '/static/img/hub-logitech-display.png'
  },
  
  // Fontes
  'fonte': {
    'logitech-display-hub': '/static/img/fonte-logitech-display-hub.png',
    'logitech-table-hub': '/static/img/fonte-logitech-table-hub.png',
    'logitech-tap': '/static/img/fonte-logitech-tap.png',
    'logitech-meetup': '/static/img/fonte-logitech-meetup.png',
    'meetup': '/static/img/fonte-logitech-meetup.png',
    'universal-chromebox': '/static/img/fonte-universal-chromebox.png',
    'chromebox': '/static/img/fonte-universal-chromebox.png',
    'universal': '/static/img/fonte-universal-chromebox.png',
    'display-hub': '/static/img/fonte-logitech-display-hub.png',
    'table-hub': '/static/img/fonte-logitech-table-hub.png',
    'tap': '/static/img/fonte-logitech-tap.png',
    'display hub': '/static/img/fonte-logitech-display-hub.png',
    'table hub': '/static/img/fonte-logitech-table-hub.png',
    'logitech': '/static/img/fonte-logitech-display-hub.png',
    'default': '/static/img/fonte-logitech-display-hub.png'
  },
  
  // TAP
  'tap': {
    'logitech-tap-poe': '/static/img/tap-logitech-tap-poe.png',
    'logitech-tap-usb': '/static/img/tap-logitech-tap-usb.png',
    'logitech': '/static/img/tap-logitech-tap-poe.png',
    'default': '/static/img/tap-logitech-tap-poe.png'
  },
  
  // PCs/Chromebox
  'pc': {
    'ctl': '/static/img/pc-ctl-outro.png',
    'bluetech': '/static/img/pc-bluetech-bluetech.png',
    'default': '/static/img/pc-ctl-outro.png'
  },
  
  // Painéis
  'painel': {
    'crestron-tsw-770-b-s': '/static/img/painel-crestron-tsw-770-b-s.png',
    'crestron-tsw-770-w-s': '/static/img/painel-crestron-tsw-770-w-s.png',
    'agenda': '/static/img/painel-crestron-tsw-770-b-s.png',
    'controle': '/static/img/painel-crestron-outro.png',
    'control': '/static/img/painel-crestron-outro.png',
    'crestron': '/static/img/painel-crestron-tsw-770-b-s.png',
    'default': '/static/img/painel-crestron-tsw-770-b-s.png'
  },
  
  // Dongles
  'dongle': {
    'logitech': '/static/img/dongle-logitech-logitech.png',
    'default': '/static/img/dongle-logitech-logitech.png'
  },
  
  // Adaptadores
  'adaptador': {
    'kramer-hdmi-f-to-hdmi-f': '/static/img/adaptador-kramer-hdmi-f-to-hdmi-f.png',
    'kramer-hdmi': '/static/img/adaptador-kramer-hdmi-f-to-hdmi-f.png',
    'usba-to-hdmi': '/static/img/adaptador-generico-usba-to-hdmi.png',
    'usb-a-to-hdmi': '/static/img/adaptador-generico-usba-to-hdmi.png',
    'usb to hdmi': '/static/img/adaptador-generico-usba-to-hdmi.png',
    'usba to hdmi': '/static/img/adaptador-generico-usba-to-hdmi.png',
    'usba to hdmi': '/static/img/adaptador-generico-usba-to-hdmi.png',
    'usb': '/static/img/adaptador-outro-usba-f-to-usba-F.png',
    'kramer': '/static/img/adaptador-kramer-hdmi-f-to-hdmi-f.png',
    'default': '/static/img/adaptador-generico-usba-to-hdmi.png'
  },
  
  // TVs
  'tv': {
    'lg-32lm621cbsb': '/static/img/tv-lg-32lm621cbsb.png',
    'lg-32SM5KE-BJ': '/static/img/tv-lg-32SM5KE-BJ.png',
    'lg-43UN731C0SC': '/static/img/tv-lg-43UN731C0SC.png',
    'lg-50ul3g-bj': '/static/img/tv-lg-50ul3g-bj.png',
    'lg-50un731c0sc': '/static/img/tv-lg-50un731c0sc.png',
    'lg-50up751c0sf': '/static/img/tv-lg-50up751c0sf.png',
    'lg-55un731c0sc': '/static/img/tv-lg-55un731c0sc.png',
    'lg-55up751c0sf': '/static/img/tv-lg-55up751c0sf.png',
    'lg-75un801c0sb': '/static/img/tv-lg-75un801c0sb.png',
    'lg-75UP801C0SB': '/static/img/tv-lg-75UP801C0SB.png',
    'lg-82UN8000PSB': '/static/img/tv-lg-82UN8000PSB.png',
    'lg': '/static/img/tv-lg-outro.png',
    'default': '/static/img/tv-lg-outro.png'
  },
  
  // Extensores
  'extensores': {
    'extron-dtp-hdmi-230-tx': '/static/img/extensores-extron-dtp-hdmi-230-tx.png',
    'extron-usb-extender-plus-t': '/static/img/extensores-extron-usb-extender-plus-t.png',
    'extron-usb-extender-plus-r': '/static/img/extensores-extron-usb-extender-plus-r.png',
    'kramer-pt571': '/static/img/extensores-kramer-pt571.png',
    'pt571': '/static/img/extensores-kramer-pt571.png',
    'extron': '/static/img/extensores-extron-dtp-hdmi-230-tx.png',
    'kramer': '/static/img/extensores-kramer-pt571.png',
    'usb': '/static/img/extensores-extron-usb-extender-plus-t.png',
    'hdmi': '/static/img/extensores-extron-dtp-hdmi-230-tx.png',
    'default': '/static/img/extensores-extron-dtp-hdmi-230-tx.png'
  },
  
  // Clickshare
  'clickshare': {
    'barco-c10': '/static/img/clickshare-barco-c10.png',
    'barco-cse-200': '/static/img/clickshare-barco-cse-200.png',
    'barco': '/static/img/clickshare-barco-c10.png',
    'default': '/static/img/clickshare-barco-c10.png'
  },
  
  // Mixers
  'mixer': {
    'shure-ani22': '/static/img/mixer-shure-ani22.png',
    'shure': '/static/img/mixer-shure-ani22.png',
    'default': '/static/img/mixer-shure-ani22.png'
  },
  
  // Amplificadores
  'amplificador': {
    'qsc-dpa4.2Q': '/static/img/amplificador-qsc-dpa4.2Q.png',
    'qsc': '/static/img/amplificador-qsc-dpa4.2Q.png',
    'default': '/static/img/amplificador-qsc-dpa4.2Q.png'
  },
  
  // Switchers
  'switcher': {
    'kramer-hdmi-vs-211H2': '/static/img/switcher-kramer-hdmi-vs-211H2.png',
    'kramer': '/static/img/switcher-kramer-hdmi-vs-211H2.png',
    'extron-sw4-usb-plus': '/static/img/switcher-extron-sw4-usb-plus.png',
    'extron-sw2-usb': '/static/img/switcher-extron-sw2-usb.png',
    'extron': '/static/img/switcher-extron-sw4-usb-plus.png',
    'usb': '/static/img/switcher-extron-sw4-usb-plus.png',
    'sw4': '/static/img/switcher-extron-sw4-usb-plus.png',
    'sw2': '/static/img/switcher-extron-sw2-usb.png',
    'rgblink-x1pro-e': '/static/img/switcher-rgblink-x1pro-e.png',
    'rgblink': '/static/img/switcher-rgblink-x1pro-e.png',
    'x1pro-e': '/static/img/switcher-rgblink-x1pro-e.png',
    'scaler video': '/static/img/switcher-kramer-hdmi-vs-211H2.png',
    'scaler': '/static/img/switcher-kramer-hdmi-vs-211H2.png',
    'video': '/static/img/switcher-kramer-hdmi-vs-211H2.png',
    'default': '/static/img/switcher-kramer-hdmi-vs-211H2.png'
  },
  
  // Sensores
  'sensor': {
    'crestron-cen-odt-c-poe': '/static/img/sensor-crestron-cen-odt-c-poe.png',
    'crestron': '/static/img/sensor-crestron-cen-odt-c-poe.png',
    'default': '/static/img/sensor-crestron-cen-odt-c-poe.png'
  },
  
  // Receptores
  'receptor': {
    'shure-ulxd4q': '/static/img/receptor-shure-ulxd4q.png',
    'shure': '/static/img/receptor-shure-ulxd4q.png',
    'default': '/static/img/receptor-shure-ulxd4q.png'
  },
  
  // Projetores
  'projetor': {
    'epson': '/static/img/projetor-epson-outro.png',
    'default': '/static/img/projetor-epson-outro.png'
  },
  
  // Telas LED
  'tela led': {
    'leyard': '/static/img/tela-led-leyard-leyard.png',
    'lg': '/static/img/tela-led-lg-outro.png',
    'mgs series': '/static/img/tela-led-leyard-mgs-series.png',
    'default': '/static/img/tela-led-lg-outro.png'
  },
  
  // Controladoras
  'controladora': {
    'lg': '/static/img/controladora-lg-outro.png',
    'leyard': '/static/img/controladora-leyard-outro.png',
    'nova star': '/static/img/controladora-nova-star-mctrl700.png',
    'mctrl700': '/static/img/controladora-nova-star-mctrl700.png',
    'default': '/static/img/controladora-lg-outro.png'
  },
  
  // Serial
  'serial': {
    'controlart-rs-232': '/static/img/serial-controlart-rs-232.png',
    'controlart': '/static/img/serial-controlart-rs-232.png',
    'default': '/static/img/serial-controlart-rs-232.png'
  },
  
  // POE
  'poe': {
    'logitech': '/static/img/poe-logitech-kit-cat5e.png',
    'default': '/static/img/poe-logitech-kit-cat5e.png'
  },
  
  // Antenas
  'antena': {
    'shure-ua864': '/static/img/antena-shure-ua864.png',
    'shure': '/static/img/antena-shure-ua864.png',
    'default': '/static/img/antena-shure-ua864.png'
  },
  
  // Meetup
  'meetup': {
    'logitech': '/static/img/meetup-logitech-meetup.png',
    'default': '/static/img/meetup-logitech-meetup.png'
  },
  
  // Splitters
  'splitter': {
    'logitech-rally-camera-power-splitter': '/static/img/splitter-logitech-rally-camera-power-splitter.png',
    'rally-camera-power-splitter': '/static/img/splitter-logitech-rally-camera-power-splitter.png',
    'camera-power-splitter': '/static/img/splitter-logitech-rally-camera-power-splitter.png',
    'power-splitter': '/static/img/splitter-logitech-rally-camera-power-splitter.png',
    'logitech': '/static/img/splitter-logitech-rally-camera-power-splitter.png',
    'default': '/static/img/splitter-logitech-rally-camera-power-splitter.png'
  },
  
  // Outros equipamentos (Ponto Usuário HDMI, Ponto Usuário USB, etc.)
  'outro': {
    'ponto usuário hdmi': '/static/img/outro-outro-outro.png',
    'ponto usuário usb': '/static/img/outro-outro-outro.png',
    'ponto usuario hdmi': '/static/img/outro-outro-outro.png',
    'ponto usuario usb': '/static/img/outro-outro-outro.png',
    'default': '/static/img/outro-outro-outro.png'
  }
};

// Função para encontrar a imagem mais adequada baseada no tipo e nome do equipamento
function findEquipmentImageByType(equipmentType, equipmentName = '', equipmentMarca = '', equipmentModelo = '') {
  const type = equipmentType.toLowerCase();
  const name = equipmentName.toLowerCase();
  const marca = equipmentMarca.toLowerCase();
  const modelo = equipmentModelo.toLowerCase();
  
  console.log('🔍 Procurando imagem para:', { type, name, marca, modelo });
  
  // Verificar se existe mapeamento para este tipo
  if (!equipmentImageMap[type]) {
    console.log('⚠️ Tipo não encontrado no mapeamento:', type);
    return null;
  }
  
  const typeMap = equipmentImageMap[type];
  
  // 1. Tentar encontrar por modelo específico primeiro (mais específico)
  if (type === 'microfone') {
    // Verificar modelos específicos de microfones (ordem específica para evitar conflitos)
    if (name.includes('mxa 710') || name.includes('mxa710') || modelo.includes('mxa710')) {
      console.log('✅ Microfone MXA 710 detectado:', typeMap['shure-mxa710']);
      return typeMap['shure-mxa710'];
    }
    if (name.includes('mxa 910') || name.includes('mxa910') || modelo.includes('mxa910')) {
      console.log('✅ Microfone MXA 910 detectado:', typeMap['shure-mxa910']);
      return typeMap['shure-mxa910'];
    }
    if (name.includes('mxa 920') || name.includes('mxa920') || modelo.includes('mxa920')) {
      console.log('✅ Microfone MXA 920 detectado:', typeMap['shure-mxa920']);
      return typeMap['shure-mxa920'];
    }
    if (name.includes('blx1') || name.includes('blx 1') || modelo.includes('blx1')) {
      console.log('✅ Microfone BLX1 detectado:', typeMap['shure-blx1']);
      return typeMap['shure-blx1'];
    }
    if (name.includes('sm58') || modelo.includes('sm58')) {
      console.log('✅ Microfone SM58 detectado:', typeMap['shure-sm58']);
      return typeMap['shure-sm58'];
    }
    if (name.includes('rally mic pod') || name.includes('rally-mic-pod') || modelo.includes('rally mic pod') || modelo.includes('rally-mic-pod')) {
      console.log('✅ Microfone Rally Mic Pod detectado:', typeMap['logitech-rally-mic-pod']);
      return typeMap['logitech-rally-mic-pod'];
    }
    if (name.includes('jabra speak') || modelo.includes('jabra speak')) {
      console.log('✅ Microfone Jabra Speak detectado:', typeMap['jabra-speak']);
      return typeMap['jabra-speak'];
    }
  }
  
  if (type === 'speaker') {
    // Verificar modelos específicos de speakers
    if (name.includes('mxn5w-c') || name.includes('mxn5w c') || modelo.includes('mxn5w-c') || modelo.includes('mxn5w c')) {
      console.log('✅ Speaker MXN5W-C detectado:', typeMap['shure-mxn5w-c']);
      return typeMap['shure-mxn5w-c'];
    }
    if (name.includes('rally') || modelo.includes('rally')) {
      console.log('✅ Speaker Rally detectado:', typeMap['logitech-rally']);
      return typeMap['logitech-rally'];
    }
    if (name.includes('jbl cbt') || name.includes('cbt 1000e') || modelo.includes('jbl cbt') || modelo.includes('cbt 1000e')) {
      console.log('✅ Speaker JBL CBT detectado:', typeMap['jbl-cbt']);
      return typeMap['jbl-cbt'];
    }
  }
  
  if (type === 'switcher') {
    // Verificar modelos específicos de switchers
    if (name.includes('scaler video') || name.includes('scaler-video') || modelo.includes('scaler video') || modelo.includes('scaler-video') || name.includes('scaler') || modelo.includes('scaler')) {
      console.log('✅ Switcher Scaler Video detectado:', typeMap['scaler video']);
      return typeMap['scaler video'];
    }
    if (name.includes('sw4') || name.includes('sw 4') || modelo.includes('sw4') || modelo.includes('sw 4') || name.includes('4ch') || modelo.includes('4ch')) {
      console.log('✅ Switcher SW4 detectado:', typeMap['extron-sw4-usb-plus']);
      return typeMap['extron-sw4-usb-plus'];
    }
    if (name.includes('sw2') || name.includes('sw 2') || modelo.includes('sw2') || modelo.includes('sw 2') || name.includes('2ch') || modelo.includes('2ch')) {
      console.log('✅ Switcher SW2 detectado:', typeMap['extron-sw2-usb']);
      return typeMap['extron-sw2-usb'];
    }
    if (name.includes('usb') || modelo.includes('usb')) {
      console.log('✅ Switcher USB detectado:', typeMap['usb']);
      return typeMap['usb'];
    }
    if (name.includes('hdmi') || modelo.includes('hdmi')) {
      console.log('✅ Switcher HDMI detectado:', typeMap['kramer-hdmi-vs-211H2']);
      return typeMap['kramer-hdmi-vs-211H2'];
    }
    if (name.includes('rgblink') || name.includes('x1pro-e') || modelo.includes('rgblink') || modelo.includes('x1pro-e') || marca.includes('rgblink')) {
      console.log('✅ Switcher RGBlink X1PRO-E detectado:', typeMap['rgblink-x1pro-e']);
      return typeMap['rgblink-x1pro-e'];
    }
  }
  
  if (type === 'extensores') {
    // Verificar modelos específicos de extensores
    if (name.includes('pt571') || name.includes('pt 571') || modelo.includes('pt571') || modelo.includes('pt 571')) {
      console.log('✅ Extensor Kramer PT571 detectado:', typeMap['kramer-pt571']);
      return typeMap['kramer-pt571'];
    }
    if (name.includes('usb extender plus r') || name.includes('usb-extender-plus-r') || modelo.includes('usb extender plus r') || modelo.includes('usb-extender-plus-r') || name.includes('plus r') || modelo.includes('plus r')) {
      console.log('✅ Extensor USB Plus R detectado:', typeMap['extron-usb-extender-plus-r']);
      return typeMap['extron-usb-extender-plus-r'];
    }
    if (name.includes('usb extender plus t') || name.includes('usb-extender-plus-t') || modelo.includes('usb extender plus t') || modelo.includes('usb-extender-plus-t') || name.includes('plus t') || modelo.includes('plus t')) {
      console.log('✅ Extensor USB Plus T detectado:', typeMap['extron-usb-extender-plus-t']);
      return typeMap['extron-usb-extender-plus-t'];
    }
    if (name.includes('dtp hdmi') || name.includes('dtp-hdmi') || modelo.includes('dtp hdmi') || modelo.includes('dtp-hdmi') || name.includes('hdmi 230') || modelo.includes('hdmi 230')) {
      console.log('✅ Extensor DTP HDMI detectado:', typeMap['extron-dtp-hdmi-230-tx']);
      return typeMap['extron-dtp-hdmi-230-tx'];
    }
    if (name.includes('usb') || modelo.includes('usb')) {
      console.log('✅ Extensor USB detectado:', typeMap['usb']);
      return typeMap['usb'];
    }
    if (name.includes('hdmi') || modelo.includes('hdmi')) {
      console.log('✅ Extensor HDMI detectado:', typeMap['hdmi']);
      return typeMap['hdmi'];
    }
  }
  
  if (type === 'avio') {
    // Verificar modelos específicos de AVIO Dante
    if (name.includes('2ch analog output') || name.includes('2ch-analog-output') || modelo.includes('2ch analog output') || modelo.includes('2ch-analog-output') || modelo.includes('2CH Analog Output Adapter')) {
      console.log('✅ AVIO Dante 2CH Analog Output detectado:', typeMap['dante-2ch-analog-output']);
      return typeMap['dante-2ch-analog-output'];
    }
    if (name.includes('2ch analog input') || name.includes('2ch-analog-input') || modelo.includes('2ch analog input') || modelo.includes('2ch-analog-input') || modelo.includes('2CH Analog Input Adapter')) {
      console.log('✅ AVIO Dante 2CH Analog Input detectado:', typeMap['dante-2ch-analog-input']);
      return typeMap['dante-2ch-analog-input'];
    }
    if (name.includes('1ch analog output') || name.includes('1ch-analog-output') || modelo.includes('1ch analog output') || modelo.includes('1ch-analog-output') || modelo.includes('1CH Analog Output Adapter')) {
      console.log('✅ AVIO Dante 1CH Analog Output detectado:', typeMap['dante-1ch-analog-output']);
      return typeMap['dante-1ch-analog-output'];
    }
    if (name.includes('1ch analog input') || name.includes('1ch-analog-input') || modelo.includes('1ch analog input') || modelo.includes('1ch-analog-input') || modelo.includes('1CH Analog Input Adapter')) {
      console.log('✅ AVIO Dante 1CH Analog Input detectado:', typeMap['dante-1ch-analog-input']);
      return typeMap['dante-1ch-analog-input'];
    }
    if (name.includes('2ch usb io') || name.includes('2ch-usb-io') || modelo.includes('2ch usb io') || modelo.includes('2ch-usb-io') || modelo.includes('2CH USB IO Adapter')) {
      console.log('✅ AVIO Dante 2CH USB IO detectado:', typeMap['dante-2ch-usb-io']);
      return typeMap['dante-2ch-usb-io'];
    }
    // Verificar se é analógico (priorizar sobre USB)
    if (name.includes('analog') || modelo.includes('analog')) {
      if (name.includes('input') || modelo.includes('input')) {
        if (name.includes('2ch') || modelo.includes('2ch') || modelo.includes('2CH')) {
          console.log('✅ AVIO Dante 2CH Analog Input detectado por analog+input:', typeMap['dante-2ch-analog-input']);
          return typeMap['dante-2ch-analog-input'];
        } else {
          console.log('✅ AVIO Dante 1CH Analog Input detectado por analog+input:', typeMap['dante-1ch-analog-input']);
          return typeMap['dante-1ch-analog-input'];
        }
      } else {
        if (name.includes('2ch') || modelo.includes('2ch') || modelo.includes('2CH')) {
          console.log('✅ AVIO Dante 2CH Analog Output detectado por analog:', typeMap['dante-2ch-analog-output']);
          return typeMap['dante-2ch-analog-output'];
        } else {
          console.log('✅ AVIO Dante 1CH Analog Output detectado por analog:', typeMap['dante-1ch-analog-output']);
          return typeMap['dante-1ch-analog-output'];
        }
      }
    }
    // Verificar se é USB
    if (name.includes('usb') || modelo.includes('usb')) {
      console.log('✅ AVIO Dante USB detectado:', typeMap['dante-2ch-usb-io']);
      return typeMap['dante-2ch-usb-io'];
    }
  }
  
  if (type === 'hub') {
    // Verificar modelos específicos de Hubs
    if (name.includes('mic pod') || name.includes('mic-pod') || modelo.includes('mic pod') || modelo.includes('mic-pod')) {
      console.log('✅ Hub Mic Pod detectado:', typeMap['logitech-mic-pod']);
      return typeMap['logitech-mic-pod'];
    }
    if (name.includes('display') || modelo.includes('display')) {
      console.log('✅ Hub Display detectado:', typeMap['logitech-display']);
      return typeMap['logitech-display'];
    }
    if (name.includes('table') || modelo.includes('table')) {
      console.log('✅ Hub Table detectado:', typeMap['logitech-table']);
      return typeMap['logitech-table'];
    }
  }
  
  if (type === 'adaptador') {
    // Verificar modelos específicos de Adaptadores
    // Detectar adaptadores USB A to HDMI especificamente
    if ((name.includes('usb') && name.includes('hdmi')) || 
        (modelo.includes('usb') && modelo.includes('hdmi')) ||
        (name.includes('usba') && name.includes('hdmi')) ||
        (modelo.includes('usba') && modelo.includes('hdmi')) ||
        (name.toLowerCase().includes('usba to hdmi')) ||
        (modelo.toLowerCase().includes('usba to hdmi'))) {
      console.log('✅ Adaptador USB A to HDMI detectado:', typeMap['usba-to-hdmi']);
      return typeMap['usba-to-hdmi'];
    }
    // Detectar adaptadores Kramer HDMI
    if ((name.includes('kramer') && name.includes('hdmi')) || 
        (modelo.includes('kramer') && modelo.includes('hdmi')) ||
        (marca && marca.includes('kramer') && (name.includes('hdmi') || modelo.includes('hdmi')))) {
      console.log('✅ Adaptador Kramer HDMI detectado:', typeMap['kramer-hdmi']);
      return typeMap['kramer-hdmi'];
    }
  }
  
  if (type === 'fonte') {
    // Verificar modelos específicos de Fontes
    if (name.includes('meetup') || modelo.includes('meetup')) {
      console.log('✅ Fonte Logitech Meetup detectado:', typeMap['logitech-meetup']);
      return typeMap['logitech-meetup'];
    }
    if (name.includes('chromebox') || modelo.includes('chromebox')) {
      console.log('✅ Fonte Universal Chromebox detectado:', typeMap['universal-chromebox']);
      return typeMap['universal-chromebox'];
    }
    if (name.includes('display hub') || name.includes('display-hub') || modelo.includes('display hub') || modelo.includes('display-hub')) {
      console.log('✅ Fonte Display Hub detectado:', typeMap['logitech-display-hub']);
      return typeMap['logitech-display-hub'];
    }
    if (name.includes('table hub') || name.includes('table-hub') || modelo.includes('table hub') || modelo.includes('table-hub')) {
      console.log('✅ Fonte Table Hub detectado:', typeMap['logitech-table-hub']);
      return typeMap['logitech-table-hub'];
    }
    if (name.includes('tap') || modelo.includes('tap')) {
      console.log('✅ Fonte TAP detectado:', typeMap['logitech-tap']);
      return typeMap['logitech-tap'];
    }
  }
  
  if (type === 'painel') {
    // Verificar tipos específicos de painéis Crestron
    if (name.includes('agenda')) {
      console.log('✅ Painel Agenda detectado:', typeMap['agenda']);
      return typeMap['agenda'];
    }
    if (name.includes('controle') || name.includes('control')) {
      console.log('✅ Painel de Controle detectado:', typeMap['controle']);
      return typeMap['controle'];
    }
    // Verificar modelos específicos
    if (name.includes('tsw-770-b-s') || modelo.includes('tsw-770-b-s')) {
      console.log('✅ Painel Crestron TSW-770-B-S detectado:', typeMap['crestron-tsw-770-b-s']);
      return typeMap['crestron-tsw-770-b-s'];
    }
    if (name.includes('tsw-770-w-s') || modelo.includes('tsw-770-w-s')) {
      console.log('✅ Painel Crestron TSW-770-W-S detectado:', typeMap['crestron-tsw-770-w-s']);
      return typeMap['crestron-tsw-770-w-s'];
    }
  }
  
  if (type === 'tela led') {
    // Verificar modelos específicos de Telas LED
    if (name.includes('mgs series') || name.includes('mgs-series') || modelo.includes('mgs series') || modelo.includes('mgs-series') || modelo.includes('MGS Series')) {
      console.log('✅ Tela LED MGS Series detectado:', typeMap['mgs series']);
      return typeMap['mgs series'];
    }
    if (name.includes('leyard') || modelo.includes('leyard')) {
      console.log('✅ Tela LED Leyard detectado:', typeMap['leyard']);
      return typeMap['leyard'];
    }
    if (name.includes('lg') || modelo.includes('lg')) {
      console.log('✅ Tela LED LG detectado:', typeMap['lg']);
      return typeMap['lg'];
    }
  }
  
  if (type === 'controladora') {
    // Verificar modelos específicos de Controladoras
    if (name.includes('mctrl700') || name.includes('mctrl 700') || modelo.includes('mctrl700') || modelo.includes('mctrl 700') || modelo.includes('MCTRL700')) {
      console.log('✅ Controladora MCTRL700 detectado:', typeMap['mctrl700']);
      return typeMap['mctrl700'];
    }
    if (name.includes('nova star') || name.includes('nova-star') || marca.includes('nova star') || marca.includes('nova-star')) {
      console.log('✅ Controladora Nova Star detectado:', typeMap['nova star']);
      return typeMap['nova star'];
    }
    if (name.includes('leyard') || modelo.includes('leyard')) {
      console.log('✅ Controladora Leyard detectado:', typeMap['leyard']);
      return typeMap['leyard'];
    }
    if (name.includes('lg') || modelo.includes('lg')) {
      console.log('✅ Controladora LG detectado:', typeMap['lg']);
      return typeMap['lg'];
    }
  }
  
  if (type === 'splitter') {
    // Verificar modelos específicos de Splitters
    if (name.includes('rally camera power splitter') || name.includes('rally-camera-power-splitter') || modelo.includes('rally camera power splitter') || modelo.includes('rally-camera-power-splitter') || name.includes('camera power splitter') || modelo.includes('camera power splitter')) {
      console.log('✅ Splitter Rally Camera Power detectado:', typeMap['logitech-rally-camera-power-splitter']);
      return typeMap['logitech-rally-camera-power-splitter'];
    }
    if (name.includes('power splitter') || modelo.includes('power splitter')) {
      console.log('✅ Splitter Power detectado:', typeMap['power-splitter']);
      return typeMap['power-splitter'];
    }
    if (name.includes('logitech') || marca.includes('logitech')) {
      console.log('✅ Splitter Logitech detectado:', typeMap['logitech']);
      return typeMap['logitech'];
    }
  }
  
  // 2. Tentar encontrar por nome específico (mais específico)
  // Ordenar por especificidade (mais específico primeiro)
  const sortedEntries = Object.entries(typeMap)
    .filter(([key]) => key !== 'default')
    .sort(([a], [b]) => {
      // Priorizar termos mais específicos
      const aWords = a.split('-').length;
      const bWords = b.split('-').length;
      if (aWords !== bWords) return bWords - aWords; // Mais palavras = mais específico
      
      // Para AVIO, não priorizar "usb" sobre "dante" para evitar conflitos
      if (type !== 'avio') {
        // Se tiverem o mesmo número de palavras, priorizar "usb" sobre "dante"
        if (a.includes('usb') && !b.includes('usb')) return -1;
        if (b.includes('usb') && !a.includes('usb')) return 1;
      }
      
      return 0;
    });
  
  for (const [key, imagePath] of sortedEntries) {
    if (name.includes(key.replace('-', ' '))) {
      console.log('✅ Imagem encontrada por nome específico:', key, imagePath);
      return imagePath;
    }
  }
  
  // 3. Tentar encontrar por fabricante com priorização inteligente
  let fabricantes = ['shure', 'logitech', 'jbl', 'kramer', 'crestron', 'lg', 'extron', 'barco', 'qsc', 'epson', 'leyard', 'controlart', 'jabra', 'huddly', 'yealink', 'bluetech', 'ctl', 'nova star'];
  
  // Se for speaker, reorganizar para priorizar logitech
  if (type === 'speaker') {
    fabricantes = ['logitech', 'jbl', 'shure', 'kramer', 'crestron', 'lg', 'extron', 'barco', 'qsc', 'epson', 'leyard', 'controlart', 'jabra', 'huddly', 'yealink', 'bluetech', 'ctl'];
  }
  // Se for microfone, reorganizar para priorizar logitech sobre shure
  else if (type === 'microfone') {
    fabricantes = ['logitech', 'jabra', 'shure', 'kramer', 'crestron', 'lg', 'extron', 'barco', 'qsc', 'epson', 'leyard', 'controlart', 'huddly', 'yealink', 'bluetech', 'ctl'];
  }
  
  // Primeiro verificar se a marca está disponível e corresponde a um fabricante
  if (marca) {
    for (const fabricante of fabricantes) {
      if (marca.includes(fabricante) && typeMap[fabricante]) {
        console.log('✅ Imagem encontrada por marca:', fabricante, typeMap[fabricante]);
        return typeMap[fabricante];
      }
    }
  }
  
  // Se não encontrou por marca, tentar por nome
  for (const fabricante of fabricantes) {
    if (name.includes(fabricante) && typeMap[fabricante]) {
      console.log('✅ Imagem encontrada por fabricante no nome:', fabricante, typeMap[fabricante]);
      return typeMap[fabricante];
    }
  }
  
  // 4. Usar imagem padrão do tipo
  if (typeMap.default) {
    console.log('✅ Usando imagem padrão do tipo:', typeMap.default);
    return typeMap.default;
  }
  
  console.log('❌ Nenhuma imagem encontrada para:', type);
  return null;
}

// Exportar para uso global
window.equipmentImageMap = equipmentImageMap;
window.findEquipmentImageByType = findEquipmentImageByType;

// Função de teste para debug
window.testAdapterMapping = function() {
  console.log('🧪 Testando mapeamento de adaptadores...');
  
  const testCases = [
    { type: 'adaptador', name: 'USBA to HDMI', marca: 'Generico', modelo: 'USBA to HDMI' },
    { type: 'adaptador', name: 'USB A to HDMI', marca: 'Generico', modelo: 'USB A to HDMI' },
    { type: 'adaptador', name: 'Adaptador USB HDMI', marca: 'Generico', modelo: 'USB to HDMI' },
    { type: 'adaptador', name: 'Kramer HDMI', marca: 'Kramer', modelo: 'HDMI F to HDMI F' }
  ];
  
  testCases.forEach((testCase, index) => {
    console.log(`\n🧪 Teste ${index + 1}:`, testCase);
    const result = findEquipmentImageByType(testCase.type, testCase.name, testCase.marca, testCase.modelo);
    console.log(`✅ Resultado:`, result);
  });
};

// Função de teste para microfones
window.testMicrophoneMapping = function() {
  console.log('🧪 Testando mapeamento de microfones...');
  
  const testCases = [
    { type: 'microfone', name: 'MXA 710', marca: 'Shure', modelo: 'MXA710' },
    { type: 'microfone', name: 'MXA 920', marca: 'Shure', modelo: 'MXA920' },
    { type: 'microfone', name: 'MXA 910', marca: 'Shure', modelo: 'MXA910' },
    { type: 'microfone', name: 'Microfone MXA 710', marca: 'Shure', modelo: 'MXA710' }
  ];
  
  testCases.forEach((testCase, index) => {
    console.log(`\n🧪 Teste Microfone ${index + 1}:`, testCase);
    const result = findEquipmentImageByType(testCase.type, testCase.name, testCase.marca, testCase.modelo);
    console.log(`✅ Resultado:`, result);
  });
}; 