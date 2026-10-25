package {
 import fe.loc.Location;
 import fe.loc.Tile;
 public class RayTestLocation extends Location {
  public var failAt:int=-1;
  public function RayTestLocation(w:int,h:int){
   spaceX=w;spaceY=h;space=[];
   for(var x:int=0;x<w;x++){
    space[x]=[];for(var y:int=0;y<h;y++){var t:Tile=new Tile();t.opac=0;t.water=0;space[x][y]=t;}
   }
  }
  override public function getTile(x:int,y:int):Tile{
   if(x+y*spaceX==failAt)throw new Error("injected incomplete refresh");
   if(x<0||y<0||x>=spaceX||y>=spaceY){var outside:Tile=new Tile();outside.opac=1;return outside;}
   return space[x][y];
  }
 }
}
