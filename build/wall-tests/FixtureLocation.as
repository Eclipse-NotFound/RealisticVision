package {
  import fe.loc.Location;
  import fe.loc.Tile;
  public class FixtureLocation extends Location {
    public var tiles:Array=[];
    public function FixtureLocation() {
      spaceX=12; spaceY=10; id="wall-fixture"; active=true; black=true;
      lDist1=1000; lDist2=1500;
      for(var y:int=0;y<spaceY;y++) for(var x:int=0;x<spaceX;x++) {
        var t:Tile=new Tile();
        t.opac=(y>=3 && y<=6)?1:0; t.phis=t.opac?1:0;
        t.visi=t.t_visi=(y==4 || y==5 || y==6)?0:1;
        tiles[x+y*spaceX]=t;
      }
    }
    override public function getTile(x:int,y:int):Tile {
      if(x<0 || y<0 || x>=spaceX || y>=spaceY) {var t:Tile=new Tile();t.opac=1;return t;}
      return tiles[x+y*spaceX];
    }
  }
}
