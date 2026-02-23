require 'sinatra'
require 'json'
require 'sequel'
require 'erô'ª>Y5x­áýâÊøsjÐRquel.connect("sqlite://app.db?readonly=true&journal_mode=memory")

get '/' do
  send_file File.join(settings.public_folder, 'index.html')
end

post '/name' do
  { message: "DEXÉU5ci|G'BÓ5©íÒåu|2X{
fH¶U0#=H;¯àôUtd	ÞÝg¯ÔÛ¡NªÊª³¦«Ü4>}1oìÎ|râÈ¬çàYº×Ãi1,¢cY¸·¸}èSÓ¦ñs*(êæw?Ú8%#´ý+<}.to_json
end

get '/highscores' do
  content_type :json
  begin
    scores =MïaÞÓa6b3}qo½sì/À¦û-ëJ%kn_-«~¾ENn+¦öçwnÏL¤`\ìñQ"oâ¥`D¨[¯¯­i®üp¸4hÊbClþÏRjîpË[Þ+d1X³yf»Qfq¤#îûÚò.ðÎvú|?q`¡Ï·ë5ª³êÈÜò5
¸µáèould not retrieve highscores: #{e.message}" }.to_json
  end
end

post '/upload-highscore' do
  playerName = requR<¬#x-©svj­¢¼A¥è&o)z£Úfî^ $üo¦júæ¾¹î4l¬X­h¦'É×CO¬Aä1=ú8Ì­,ðêp/QÉ`î£mùÎúzà»§f&ä(Â8V7$XPgFìÕP³ÈÎè}avè">ääü´é?$SAF=:ë/¤µE '¬]I$wä,CgAà
 Ä¾¹
KÇB«g>ìJ_JjÓÛFÉ<å¦K3O)&«ã­GÜ®öAS¿,¥àµ6ë·GÜÔbß¹ØñèþgÂ ×dµùèíæSæ%/T{Ñùß]´ë±CÒ9Ë7äÊ-ºHO¬þ²Á½@ß]©Èzê²úkvpsYpcä§ðbhm70ÐE´³ßtent_type :json
    { message: result }.to_json

  rescue SecurityError => e
    status 403
    { message: "SECURITY BLOCKED: #{e.message}" }.to_json
  rescue Exception => e
    status 500
    { message: "Error: #{e.message}" }.to_json
  end
end
