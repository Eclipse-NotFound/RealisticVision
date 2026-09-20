package {
  import fe.loc.Location;
  import fe.loc.Tile;
  public class MotionLocation extends Location {
    public var tiles:Array=[];
    public function MotionLocation() {
      spaceX=24;spaceY=18;id="motion-corner";active=true;black=true;
      lDist1=2000;lDist2=2500;units=[];
      for(var y:int=0;y<spaceY;y++)for(var x:int=0;x<spaceX;x++){
        var t:Tile=new Tile();t.opac=(x==10 && y>=6 && y<=10)?1:0;t.phis=t.opac?1:0;
        t.visi=t.t_visi=t.opac?0:1;tiles[x+y*spaceX]=t;
      }
    }
    override public function getTile(x:int,y:int):Tile {
      if(x<0||y<0||x>=spaceX||y>=spaceY){var t:Tile=new Tile();t.opac=1;return t;}
      return tiles[x+y*spaceX];
    }
  }
}
